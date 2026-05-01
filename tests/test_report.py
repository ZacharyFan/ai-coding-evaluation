import json
from pathlib import Path

from scripts.report import collect_runs


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_report_collects_score_json_and_merges_run_facts(tmp_path):
    run_dir = tmp_path / "runs" / "baseline" / "task" / "demo"
    write_json(
        run_dir / "run.json",
        {
            "workflow_id": "baseline",
            "task_id": "task",
            "duration_minutes": 2,
            "human_interventions": 1,
            "tests": {"required_passed": True, "hidden_passed": None},
        },
    )
    write_json(
        run_dir / "score.json",
        {
            "workflow_id": "baseline",
            "task_id": "task",
            "score": 82,
            "attention_adjusted_score": 82,
            "hard_gates": [],
        },
    )

    runs = collect_runs(tmp_path / "runs")

    assert len(runs) == 1
    assert runs[0]["score"] == 82
    assert runs[0]["duration_minutes"] == 2
    assert runs[0]["tests"]["required_passed"] is True


def test_report_treats_draft_score_json_as_unscored(tmp_path):
    run_dir = tmp_path / "runs" / "baseline" / "task" / "demo"
    write_json(
        run_dir / "run.json",
        {
            "workflow_id": "baseline",
            "task_id": "task",
            "duration_minutes": 2,
            "human_interventions": 1,
            "tests": {"required_passed": True, "hidden_passed": None},
        },
    )
    write_json(
        run_dir / "score.json",
        {
            "workflow_id": "baseline",
            "task_id": "task",
            "review": {"correctness": None},
            "review_sources": {"correctness": "manual_pending"},
        },
    )

    runs = collect_runs(tmp_path / "runs")

    assert len(runs) == 1
    assert "score" not in runs[0]
