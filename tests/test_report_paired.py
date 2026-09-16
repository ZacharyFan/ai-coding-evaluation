import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.report import print_paired_summary
from scripts.report_data import collect_runs, paired_deltas, paired_summary

REPO_ROOT = Path(__file__).resolve().parent.parent


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_run(
    runs_root: Path,
    workflow: str,
    task: str,
    run_id: str,
    *,
    score: float | None,
    model: str = "gpt-5.5",
) -> None:
    run_dir = runs_root / workflow / task / run_id
    write_json(
        run_dir / "run.json",
        {
            "workflow_id": workflow,
            "task_id": task,
            "model": model,
            "duration_minutes": 2,
            "human_interventions": 1,
            "tests": {"required_passed": True, "hidden_passed": None},
        },
    )
    if score is not None:
        write_json(
            run_dir / "score.json",
            {
                "workflow_id": workflow,
                "task_id": task,
                "score": score,
                "attention_adjusted_score": score,
                "hard_gates": [],
            },
        )


def test_paired_deltas_diffs_candidate_arms_against_reference(tmp_path):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=82)
    write_run(runs_root, "baseline", "task-a", "r2", score=78)
    write_run(runs_root, "baseline", "task-b", "r1", score=55)
    write_run(runs_root, "plan-first", "task-a", "r1", score=88)
    write_run(runs_root, "plan-first", "task-b", "r1", score=75)
    write_run(runs_root, "plan-first", "task-c", "r1", score=70)
    write_run(runs_root, "plan-first", "task-d", "r1", score=None)

    deltas = paired_deltas(collect_runs(runs_root))

    assert [(delta["task_id"], delta["delta"]) for delta in deltas] == [
        ("task-a", 8.0),
        ("task-b", 20.0),
    ]
    assert deltas[0]["candidate_mean"] == 88.0
    assert deltas[0]["reference_mean"] == 80.0
    assert deltas[0]["workflow_id"] == "plan-first"
    assert deltas[0]["model_label"] == "gpt-5.5"


def test_paired_deltas_requires_matching_model(tmp_path):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=80)
    write_run(runs_root, "plan-first", "task-a", "r1", score=88, model="claude-sonnet-4.5")

    deltas = paired_deltas(collect_runs(runs_root))

    assert deltas == []


def test_paired_deltas_excludes_reference_workflow(tmp_path):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=80)
    write_run(runs_root, "baseline", "task-b", "r1", score=55)

    summary = paired_summary(collect_runs(runs_root))

    assert summary["pairs_total"] == 0
    assert summary["by_workflow"] == {}


def test_paired_summary_counts_arms_pairs_and_signs(tmp_path):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=80)
    write_run(runs_root, "baseline", "task-b", "r1", score=55)
    write_run(runs_root, "baseline", "task-d", "r1", score=60)
    write_run(runs_root, "plan-first", "task-a", "r1", score=88)
    write_run(runs_root, "plan-first", "task-b", "r1", score=45)
    write_run(runs_root, "plan-first", "task-c", "r1", score=70)
    write_run(runs_root, "plan-first", "task-d", "r1", score=60)

    summary = paired_summary(collect_runs(runs_root))

    entry = summary["by_workflow"]["plan-first"]
    assert entry["arms"] == 4
    assert entry["pairs"] == 3
    assert entry["coverage"] == 0.75
    assert entry["positive"] == 1
    assert entry["negative"] == 1
    assert entry["sign_consistency"] == pytest.approx(1 / 3)
    assert entry["mean_delta"] == pytest.approx(-2 / 3)


def test_paired_summary_without_reference_data(tmp_path):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "plan-first", "task-a", "r1", score=88)

    summary = paired_summary(collect_runs(runs_root))

    assert summary["pairs_total"] == 0
    entry = summary["by_workflow"]["plan-first"]
    assert entry["pairs"] == 0
    assert entry["coverage"] == 0.0
    assert entry["mean_delta"] is None
    assert entry["sign_consistency"] is None


def test_print_paired_summary_renders_table(tmp_path, capsys):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=80)
    write_run(runs_root, "baseline", "task-b", "r1", score=55)
    write_run(runs_root, "baseline", "task-c", "r1", score=70)
    write_run(runs_root, "plan-first", "task-a", "r1", score=88)
    write_run(runs_root, "plan-first", "task-b", "r1", score=75)
    write_run(runs_root, "plan-first", "task-c", "r1", score=66)

    print_paired_summary(collect_runs(runs_root), "baseline")

    output = capsys.readouterr().out
    assert "Paired vs reference workflow: baseline" in output
    assert "| plan-first | 3 | 3/3 | +8.00 | 0.67 |" in output


def test_print_paired_summary_suppresses_when_no_pairs(tmp_path, capsys):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=80)

    print_paired_summary(collect_runs(runs_root), "baseline")

    assert capsys.readouterr().out == ""


def test_report_cli_reference_workflow_flag(tmp_path):
    runs_root = tmp_path / "runs"
    write_run(runs_root, "baseline", "task-a", "r1", score=80)
    write_run(runs_root, "plan-first", "task-a", "r1", score=88)

    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.report",
            "--runs",
            str(runs_root),
            "--reference-workflow",
            "baseline",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0
    assert "Paired vs reference workflow: baseline" in process.stdout
    assert "| plan-first | 1 | 1/1 | +8.00 | 1.00 |" in process.stdout
