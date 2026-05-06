import json
from pathlib import Path

from scripts.dashboard import dashboard_html, zh_output_path
from scripts.dashboard_i18n import LOCALES
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
    adoption_defaults = {
        "candidate_ref": None,
        "accepted_ref": None,
        "ai_generated_lines": None,
        "accepted_lines": None,
        "adoption_rate": None,
    }
    run_data = {**run}
    run_data["adoption"] = {**adoption_defaults, **run.get("adoption", {})}
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
            **run_data,
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


def append_event(root: Path, workflow: str, task_id: str, run_id: str, event: dict) -> None:
    events_path = root / "runs" / workflow / task_id / run_id / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def context_event(context_type: str, context_id: str, *, empty: bool = False) -> dict:
    return {
        "hook_event": "PostToolUse",
        "tool_name": "Read",
        "action": {
            "success": True,
            "result_summary": {
                "observed": True,
                "empty": empty,
                "result_count": 0 if empty else 1,
                "output_chars": 0 if empty else 20,
                "line_count": 0 if empty else 1,
                "summary": "empty_text" if empty else "non_empty_text",
            },
        },
        "classifications": ["tool_use", "read_docs"],
        "context": {
            "type": context_type,
            "id": context_id,
            "classification_source": "configured",
        },
    }


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


def test_dashboard_table_headers_include_calculation_tooltips(tmp_path):
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

    html = dashboard_html(runs)

    assert "info-icon" in html
    assert 'id="floatingTooltip"' in html
    assert "data-tooltip-help" in html
    assert "Final score after hard gates" in html
    assert "Each cell aggregates scored runs" in html
    assert "attention_adjusted_score = score / max(1, human_interventions)" in html


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
    assert "info-icon" in html
    assert "最终分 = 原始分经过 hard gate 封顶后的结果" in html
    assert "每个单元格聚合当前筛选条件下同一任务、同一工作流的已评分 run" in html
    assert "undefined" not in html
    assert "None" not in html


def test_dashboard_html_includes_context_link_metrics(tmp_path):
    write_task(tmp_path)
    write_run(
        tmp_path,
        "baseline",
        "task",
        "hit",
        {"adoption": {"ai_generated_lines": 10, "accepted_lines": 7, "adoption_rate": None}},
        {"score": 100, "raw_score": 100, "attention_adjusted_score": 100, "hard_gates": []},
    )
    write_run(
        tmp_path,
        "baseline",
        "task",
        "miss",
        {"adoption": {"ai_generated_lines": 10, "accepted_lines": 3, "adoption_rate": None}},
        {"score": 80, "raw_score": 80, "attention_adjusted_score": 80, "hard_gates": []},
    )
    append_event(tmp_path, "baseline", "task", "hit", context_event("knowledge", "docs/contexts/catalog.md"))
    append_event(tmp_path, "baseline", "task", "miss", context_event("knowledge", "docs/contexts/catalog.md", empty=True))
    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    html = dashboard_html(runs)

    assert "Context Link Metrics" in html
    assert "Call Rate" in html
    assert "Hit Rate" in html
    assert "Adoption Rate" in html
    assert "docs/contexts/catalog.md" in html
    assert "50%" in html
    assert "true_hit" in html
    assert "undefined" not in html
    assert "None" not in html


def test_dashboard_html_context_metrics_support_chinese_locale(tmp_path):
    write_task(tmp_path)
    write_run(tmp_path, "baseline", "task", "demo", {})
    append_event(tmp_path, "baseline", "task", "demo", context_event("project_doc", "README.md"))
    runs = collect_runs(tmp_path / "runs", tmp_path / "benchmarks" / "tasks")

    html = dashboard_html(runs, "zh-CN")

    assert "链路指标" in html
    assert "调用率" in html
    assert "命中率" in html
    assert "采纳率" in html
    assert "暂无数据" in html


def test_dashboard_tooltip_text_is_escaped(tmp_path, monkeypatch):
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
    labels = json.loads(json.dumps(LOCALES["en"]))
    labels["run_headers"][8]["help"] = '<img src=x onerror="alert(1)">'
    monkeypatch.setitem(LOCALES, "test", labels)

    html = dashboard_html(runs, "test")

    assert '<img src=x onerror="alert(1)">' not in html
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in html


def test_zh_output_path_adds_locale_suffix():
    assert zh_output_path(Path("reports/dashboard.html")) == Path("reports/dashboard.zh-CN.html")
