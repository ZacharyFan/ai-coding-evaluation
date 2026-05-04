import json
from pathlib import Path

from scripts.dashboard import dashboard_html, zh_output_path
from scripts.report_data import collect_runs, summarize_runs


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_task(root: Path, task_id: str = "task") -> None:
    write_json(
        root / "benchmarks" / "tasks" / task_id / "task.json",
        {
            "id": task_id,
            "type": "bugfix",
            "effort_size": "small",
            "complexity": {
                "business_complexity": "L1_standardized",
                "context_maturity": "C1_complete",
            },
        },
    )


def write_run(root: Path, workflow: str, task_id: str, run_id: str, run: dict, score: dict | None = None) -> None:
    run_dir = root / "runs" / workflow / task_id / run_id
    write_json(
        run_dir / "run.json",
        {
            "workflow_id": workflow,
            "task_id": task_id,
            "model": "gpt-5.5",
            "duration_minutes": 2,
            "human_interventions": 1,
            "tests": {"required_passed": True, "hidden_passed": None},
            "diff": {"unrelated_files_changed": 0},
            **run,
        },
    )
    if score is not None:
        write_json(
            run_dir / "score.json",
            {
                "workflow_id": workflow,
                "task_id": task_id,
                **score,
            },
        )


def test_collect_runs_merges_task_run_and_score_data(tmp_path):
    write_task(tmp_path)
    write_run(
        tmp_path,
        "baseline",
        "task",
        "demo",
        {"model": "claude-sonnet-4.5"},
        {"score": 82, "raw_score": 90, "attention_adjusted_score": 82, "hard_gates": []},
    )

    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    assert len(runs) == 1
    assert runs[0]["run_id"] == "demo"
    assert runs[0]["model_label"] == "claude-sonnet-4.5"
    assert runs[0]["task_type"] == "bugfix"
    assert runs[0]["effort_size"] == "small"
    assert runs[0]["business_complexity"] == "L1_standardized"
    assert runs[0]["context_maturity"] == "C1_complete"
    assert runs[0]["score"] == 82
    assert runs[0]["scored"] is True


def test_collect_runs_marks_missing_or_draft_score_as_unscored(tmp_path):
    write_task(tmp_path)
    write_run(tmp_path, "baseline", "task", "missing-score", {})
    write_run(
        tmp_path,
        "baseline",
        "task",
        "draft-score",
        {},
        {"review": {"correctness": None}, "review_sources": {"correctness": "manual_pending"}},
    )

    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    assert len(runs) == 2
    assert [run["scored"] for run in runs] == [False, False]


def test_summarize_runs_uses_scored_runs_for_rates_and_averages(tmp_path):
    write_task(tmp_path)
    write_run(
        tmp_path,
        "baseline",
        "task",
        "pass",
        {"duration_minutes": 4, "human_interventions": 2},
        {"score": 90, "attention_adjusted_score": 45, "hard_gates": []},
    )
    write_run(
        tmp_path,
        "baseline",
        "task",
        "gated",
        {"tests": {"required_passed": False, "hidden_passed": None}},
        {"score": 60, "attention_adjusted_score": 60, "hard_gates": ["required_tests_failed"]},
    )
    write_run(tmp_path, "baseline", "task", "unscored", {})
    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    summary = summarize_runs(runs)

    assert summary["runs"] == 3
    assert summary["scored_runs"] == 2
    assert summary["avg_score"] == 75
    assert summary["avg_attention_score"] == 52.5
    assert summary["first_pass_rate"] == 0.5
    assert summary["gate_rate"] == 0.5


def test_dashboard_html_escapes_values_and_avoids_frontend_leaks(tmp_path):
    write_task(tmp_path)
    write_run(
        tmp_path,
        "baseline",
        "task",
        "demo",
        {"model": "<script>alert(1)</script>"},
        {"score": 100, "raw_score": 100, "attention_adjusted_score": 100, "hard_gates": []},
    )
    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    html = dashboard_html(runs)

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "undefined" not in html
    assert "None" not in html
    assert "Task × Workflow Heatmap" in html
    assert "Model Comparison" in html


def test_dashboard_html_supports_chinese_locale(tmp_path):
    write_task(tmp_path)
    write_run(
        tmp_path,
        "baseline",
        "task",
        "demo",
        {},
        {"score": 100, "raw_score": 100, "attention_adjusted_score": 100, "hard_gates": []},
    )
    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    html = dashboard_html(runs, "zh-CN")

    assert '<html lang="zh-CN">' in html
    assert "AI Coding 评估看板" in html
    assert "任务 × 工作流热力图" in html
    assert "模型对比" in html
    assert "仅看已评分" in html
    assert "undefined" not in html
    assert "None" not in html


def test_zh_output_path_adds_locale_suffix():
    assert zh_output_path(Path("reports/dashboard.html")) == Path("reports/dashboard.zh-CN.html")
