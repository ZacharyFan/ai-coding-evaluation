from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import llm_review_run as llm_review_module
from scripts.llm_review_run import build_review_prompt, llm_review_run, redact_secrets


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def base_task() -> dict:
    return {
        "id": "example-task",
        "time_budget_minutes": 10,
        "max_human_interventions": 2,
        "max_cost_usd": 1.0,
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


def base_run() -> dict:
    return {
        "workflow_id": "baseline",
        "task_id": "example-task",
        "duration_minutes": 1,
        "human_interventions": 1,
        "cost_usd": 0,
        "tests": {
            "required_passed": True,
            "hidden_passed": None,
        },
        "diff": {
            "files_changed": 1,
            "unrelated_files_changed": 0,
            "scope_check": "not_configured",
        },
        "process_evidence": {
            "project_instructions_read": False,
            "relevant_docs_read": [],
            "knowledge_sources_used": [],
            "tools_used": [],
            "plan_followed": False,
            "self_review_performed": False,
        },
    }


def write_run_files(tmp_path: Path, run: dict | None = None) -> tuple[Path, Path, Path]:
    task_dir = tmp_path / "task"
    run_dir = tmp_path / "runs" / "baseline" / "example-task" / "demo"
    task_dir.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    task_path = task_dir / "task.json"
    run_path = run_dir / "run.json"
    write_json(task_path, base_task())
    (task_dir / "task.md").write_text("# Task\nFix the behavior.\n", encoding="utf-8")
    (task_dir / "acceptance.md").write_text("# Acceptance\nThe final diff is correct.\n", encoding="utf-8")
    write_json(run_path, run or base_run())
    (run_dir / "test.log").write_text("$ test\nexit_code=0\n", encoding="utf-8")
    (run_dir / "diff.patch").write_text("diff --git a/value.txt b/value.txt\n", encoding="utf-8")
    return task_path, run_path, run_dir / "score.json"


def llm_response(review: dict | None = None) -> str:
    return json.dumps(
        {
            "review": review
            or {
                "correctness": 1.0,
                "regression_safety": 1.0,
                "maintainability": 0.8,
                "test_quality": 0.7,
                "security": 1.0,
                "process_compliance": 0.6,
            },
            "review_notes": {
                "correctness": "The required behavior is fixed.",
                "maintainability": "The diff is small and local.",
            },
        }
    )


def test_llm_review_run_uses_llm_json_and_writes_score_without_mutating_run_json(tmp_path, monkeypatch):
    task_path, run_path, score_path = write_run_files(tmp_path)

    monkeypatch.setattr(llm_review_module, "send_chat_completion", lambda **kwargs: llm_response())

    score = llm_review_run(
        task_path,
        run_path,
        score_path,
        write=True,
        base_url="https://example.com/v1",
        model="review-model",
        api_key="test-key",
    )

    persisted_run = json.loads(run_path.read_text(encoding="utf-8"))
    persisted_score = json.loads(score_path.read_text(encoding="utf-8"))
    assert "review" not in persisted_run
    assert "score" not in persisted_run
    assert persisted_score["review"]["correctness"] == 1.0
    assert persisted_score["review_sources"]["correctness"] == "llm"
    assert persisted_score["review_notes"]["maintainability"] == "The diff is small and local."
    assert persisted_score["score"] == score["score"]


def test_llm_review_run_preserves_existing_manual_gates(tmp_path, monkeypatch):
    task_path, run_path, score_path = write_run_files(tmp_path)
    write_json(score_path, {"manual_hard_gates": ["public_api_break"]})
    monkeypatch.setattr(llm_review_module, "send_chat_completion", lambda **kwargs: llm_response())

    score = llm_review_run(
        task_path,
        run_path,
        score_path,
        write=True,
        base_url="https://example.com/v1",
        model="review-model",
        api_key="test-key",
    )

    assert score["manual_hard_gates"] == ["public_api_break"]
    assert score["score"] == 55


def test_llm_review_run_invalid_llm_json_does_not_overwrite_existing_score(tmp_path, monkeypatch):
    task_path, run_path, score_path = write_run_files(tmp_path)
    write_json(score_path, {"score": 88, "review": {"correctness": 1}})
    monkeypatch.setattr(llm_review_module, "send_chat_completion", lambda **kwargs: "{not json")

    with pytest.raises(ValueError, match="LLM response is not valid JSON"):
        llm_review_run(
            task_path,
            run_path,
            score_path,
            write=True,
            base_url="https://example.com/v1",
            model="review-model",
            api_key="test-key",
        )

    assert json.loads(score_path.read_text(encoding="utf-8"))["score"] == 88


def test_llm_review_run_rejects_out_of_range_llm_scores(tmp_path, monkeypatch):
    task_path, run_path, score_path = write_run_files(tmp_path)
    bad_review = {
        "correctness": 1.2,
        "regression_safety": 1.0,
        "maintainability": 1.0,
        "test_quality": 1.0,
        "security": 1.0,
        "process_compliance": 1.0,
    }
    monkeypatch.setattr(llm_review_module, "send_chat_completion", lambda **kwargs: llm_response(bad_review))

    with pytest.raises(ValueError, match="review.correctness must be between 0 and 1"):
        llm_review_run(
            task_path,
            run_path,
            score_path,
            write=True,
            base_url="https://example.com/v1",
            model="review-model",
            api_key="test-key",
        )

    assert not score_path.exists()


def test_review_prompt_includes_acceptance_and_redacts_secrets(tmp_path):
    task_path, run_path, _ = write_run_files(tmp_path)
    (run_path.parent / "test.log").write_text("Authorization: Bearer secret-token\n", encoding="utf-8")

    prompt = build_review_prompt(task_path, run_path, max_input_chars=10_000)

    assert "The final diff is correct." in prompt
    assert "Bearer <redacted>" in prompt
    assert "secret-token" not in prompt


def test_review_prompt_fails_when_input_is_too_large(tmp_path):
    task_path, run_path, _ = write_run_files(tmp_path)
    (run_path.parent / "diff.patch").write_text("x" * 500, encoding="utf-8")

    with pytest.raises(ValueError, match="review input is too large"):
        build_review_prompt(task_path, run_path, max_input_chars=100)


def test_redact_secrets_masks_common_secret_shapes():
    text = "api_key = sk-live-secret\npassword: hunter2\nAuthorization: Bearer abc.def"

    redacted = redact_secrets(text)

    assert "sk-live-secret" not in redacted
    assert "hunter2" not in redacted
    assert "abc.def" not in redacted
