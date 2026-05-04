import json
import subprocess
import sys
from pathlib import Path

from scripts.score_run import apply_manual_review, init_score_doc, parse_review_assignment, score_run, write_initialized_score


def base_task():
    return {
        "time_budget_minutes": 30,
        "max_human_interventions": 3,
        "max_cost_usd": 2.0,
        "scoring_weights": {
            "correctness": 35,
            "regression_safety": 15,
            "maintainability": 15,
            "test_quality": 10,
            "security": 10,
            "process_compliance": 5,
            "efficiency": 10,
        },
    }


def base_run():
    return {
        "workflow_id": "baseline",
        "task_id": "example-task",
        "duration_minutes": 15,
        "human_interventions": 1,
        "cost_usd": 1.0,
        "tests": {
            "required_passed": True,
            "hidden_passed": True,
        },
        "diff": {
            "files_changed": 3,
            "unrelated_files_changed": 0,
            "scope_check": "not_configured",
        },
    }


def base_score():
    return {
        "review": {
            "correctness": 1.0,
            "regression_safety": 1.0,
            "maintainability": 1.0,
            "test_quality": 1.0,
            "security": 1.0,
            "process_compliance": 1.0,
        },
        "manual_hard_gates": [],
    }


def test_perfect_run_scores_100():
    result = score_run(base_task(), base_run(), base_score())

    assert result["score"] == 100.0
    assert result["attention_adjusted_score"] == 100.0
    assert result["hard_gates"] == []
    assert result["derived_hard_gates"] == []


def test_required_test_failure_caps_score():
    run = base_run()
    run["tests"]["required_passed"] = False

    result = score_run(base_task(), run, base_score())

    assert result["score"] == 60
    assert result["hard_gates"] == ["required_tests_failed"]


def test_unrelated_changes_are_derived_as_hard_gate():
    run = base_run()
    run["diff"]["unrelated_files_changed"] = 2

    result = score_run(base_task(), run, base_score())

    assert result["score"] == 65
    assert result["hard_gates"] == ["unrelated_changes"]


def test_attention_score_penalizes_human_interventions():
    run = base_run()
    run["human_interventions"] = 4

    result = score_run(base_task(), run, base_score())

    assert result["score"] < 100
    assert result["attention_adjusted_score"] < result["score"]


def test_security_zero_adds_security_gate():
    score = base_score()
    score["review"]["security"] = 0

    result = score_run(base_task(), base_run(), score)

    assert result["score"] == 50
    assert result["hard_gates"] == ["security_issue"]


def test_process_compliance_lowers_raw_score_without_gate():
    score = base_score()
    score["review"]["process_compliance"] = 0

    result = score_run(base_task(), base_run(), score)

    assert result["raw_score"] == 95.0
    assert result["score"] == 95.0
    assert result["hard_gates"] == []


def test_hidden_unknown_does_not_trigger_hidden_gate():
    run = base_run()
    run["tests"]["hidden_passed"] = None

    result = score_run(base_task(), run, base_score())

    assert result["score"] == 100.0
    assert "hidden_tests_failed" not in result["hard_gates"]


def test_unknown_cost_is_ignored_by_efficiency():
    run = base_run()
    run["cost_usd"] = None

    result = score_run(base_task(), run, base_score())

    assert result["score"] == 100.0
    assert result["efficiency"] == 1.0


def test_unknown_unrelated_file_count_does_not_trigger_gate():
    run = base_run()
    run["diff"]["unrelated_files_changed"] = None

    result = score_run(base_task(), run, base_score())

    assert result["score"] == 100.0
    assert "unrelated_changes" not in result["hard_gates"]


def test_old_derived_gate_does_not_stick_after_rescore():
    score = base_score()
    score["hard_gates"] = ["task_not_solved"]
    score["derived_hard_gates"] = ["task_not_solved"]

    result = score_run(base_task(), base_run(), score)

    assert result["score"] == 100.0
    assert result["hard_gates"] == []


def test_manual_gate_is_preserved():
    score = base_score()
    score["manual_hard_gates"] = ["public_api_break"]

    result = score_run(base_task(), base_run(), score)

    assert result["score"] == 55
    assert result["hard_gates"] == ["public_api_break"]


def test_init_score_doc_creates_manual_draft():
    draft = init_score_doc(base_run())

    assert draft["workflow_id"] == "baseline"
    assert draft["task_id"] == "example-task"
    assert set(draft["review"]) == {
        "correctness",
        "regression_safety",
        "maintainability",
        "test_quality",
        "security",
        "process_compliance",
    }
    assert all(value is None for value in draft["review"].values())
    assert all(value == "manual_pending" for value in draft["review_sources"].values())
    assert draft["manual_hard_gates"] == []
    assert "derived_hard_gates" not in draft
    assert "hard_gates" not in draft
    assert "score" not in draft
    assert "raw_score" not in draft


def test_write_initialized_score_refuses_to_overwrite_existing_score(tmp_path):
    score_path = tmp_path / "score.json"
    score_path.write_text('{"score": 100}\n', encoding="utf-8")

    try:
        write_initialized_score(score_path, base_run())
    except FileExistsError as error:
        assert "score file already exists" in str(error)
    else:
        raise AssertionError("expected init to refuse overwriting score.json")

    assert json.loads(score_path.read_text(encoding="utf-8")) == {"score": 100}


def test_apply_manual_review_fills_scores_and_sources():
    draft = init_score_doc(base_run())

    updated = apply_manual_review(
        draft,
        [
            "correctness=1.0",
            "regression_safety=1.0",
            "maintainability=0.8",
            "test_quality=0.8",
            "security=1.0",
            "process_compliance=0.6",
        ],
        [],
    )

    assert updated["review"]["correctness"] == 1.0
    assert updated["review"]["maintainability"] == 0.8
    assert updated["review"]["process_compliance"] == 0.6
    assert all(source == "manual" for source in updated["review_sources"].values())
    assert updated["manual_hard_gates"] == []


def test_apply_manual_review_accepts_manual_hard_gates():
    updated = apply_manual_review(base_score(), [], ["public_api_break", "public_api_break"])

    assert updated["manual_hard_gates"] == ["public_api_break"]


def test_score_run_cli_sets_manual_review_and_scores_in_one_step(tmp_path):
    task_path = tmp_path / "task.json"
    run_path = tmp_path / "run.json"
    score_path = tmp_path / "score.json"
    task_path.write_text(json.dumps(base_task()), encoding="utf-8")
    run_path.write_text(json.dumps(base_run()), encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "score_run.py"),
            "--task",
            str(task_path),
            "--run",
            str(run_path),
            "--score",
            str(score_path),
            "--set-review",
            "correctness=1.0",
            "regression_safety=1.0",
            "maintainability=0.8",
            "test_quality=0.8",
            "security=1.0",
            "process_compliance=0.6",
            "--write",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(result.stdout)
    score = json.loads(score_path.read_text(encoding="utf-8"))
    assert output["score"] == 93.0
    assert score["score"] == 93.0
    assert score["review"]["correctness"] == 1.0
    assert score["review"]["process_compliance"] == 0.6
    assert score["review_sources"]["correctness"] == "manual"


def test_parse_review_assignment_rejects_bad_input():
    for value, expected in [
        ("correctness", "dimension=value"),
        ("unknown=1", "unknown review dimension"),
        ("correctness=high", "must be a number"),
        ("correctness=1.2", "must be between 0 and 1"),
    ]:
        try:
            parse_review_assignment(value)
        except ValueError as error:
            assert expected in str(error)
        else:
            raise AssertionError(f"expected invalid review assignment to fail: {value}")


def test_incomplete_manual_review_cannot_be_scored():
    draft = init_score_doc(base_run())

    try:
        score_run(base_task(), base_run(), draft)
    except ValueError as error:
        assert "review.correctness must be filled before scoring" in str(error)
        assert "--set-review correctness=<0-1>" in str(error)
    else:
        raise AssertionError("expected incomplete manual review to fail scoring")
