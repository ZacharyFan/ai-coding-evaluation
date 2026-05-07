from __future__ import annotations

import json
from pathlib import Path

from scripts.context_metrics import collect_context_metrics


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_run(
    root: Path, workflow: str, task: str, run_id: str, *, adoption: dict | None = None
) -> Path:
    run_dir = root / workflow / task / run_id
    adoption_defaults = {
        "candidate_ref": None,
        "accepted_ref": None,
        "ai_generated_lines": None,
        "accepted_lines": None,
        "adoption_rate": None,
    }
    write_json(
        run_dir / "run.json",
        {
            "workflow_id": workflow,
            "task_id": task,
            "duration_minutes": 1,
            "human_interventions": 0,
            "tests": {"required_passed": True, "hidden_passed": None},
            "diff": {"files_changed": 1, "unrelated_files_changed": 0},
            "adoption": {**adoption_defaults, **(adoption or {})},
        },
    )
    return run_dir


def context_event(
    context_type: str, context_id: str, *, empty: bool = False, legacy: bool = False
) -> dict:
    action = {
        "kind": "read",
        "command_summary": context_id,
        "paths": [context_id],
        "success": True,
    }
    if not legacy:
        action["result_summary"] = {
            "observed": True,
            "empty": empty,
            "result_count": 0 if empty else 2,
            "output_chars": 0 if empty else 80,
            "line_count": 0 if empty else 2,
            "summary": "empty_text" if empty else "non_empty_text",
        }
    return {
        "schema_version": "1",
        "timestamp": "2026-05-02T00:00:00Z",
        "source": "codex",
        "hook_event": "PostToolUse",
        "tool_name": "Read",
        "action": action,
        "classifications": ["tool_use", "read_docs"],
        "context": {
            "type": context_type,
            "id": context_id,
            "classification_source": "configured",
        },
    }


def test_context_metrics_uses_non_empty_event_files_as_observed_runs(tmp_path):
    runs = tmp_path / "runs"
    called = write_run(runs, "baseline", "task", "called")
    append_event(called / "events.jsonl", context_event("knowledge", "docs/contexts/catalog.md"))
    write_run(runs, "baseline", "task", "empty-events").joinpath("events.jsonl").write_text(
        "", encoding="utf-8"
    )

    metrics = collect_context_metrics(runs)

    assert metrics["observed_runs"] == 1
    assert metrics["runs_with_context_call"] == 1
    assert metrics["runs_with_context_hit"] == 1
    assert metrics["call_rate"] == 1.0
    assert metrics["hit_rate"] == 1.0


def test_context_metrics_calculates_call_hit_and_adoption_rates(tmp_path):
    runs = tmp_path / "runs"
    hit = write_run(
        runs,
        "baseline",
        "task",
        "hit",
        adoption={"ai_generated_lines": 10, "accepted_lines": 7, "adoption_rate": None},
    )
    miss = write_run(
        runs,
        "baseline",
        "task",
        "miss",
        adoption={"ai_generated_lines": 10, "accepted_lines": 3, "adoption_rate": None},
    )
    no_call = write_run(runs, "baseline", "task", "no-call")
    append_event(hit / "events.jsonl", context_event("knowledge", "docs/contexts/catalog.md"))
    append_event(
        miss / "events.jsonl", context_event("knowledge", "docs/contexts/catalog.md", empty=True)
    )
    append_event(
        no_call / "events.jsonl",
        {
            "hook_event": "PostToolUse",
            "action": {"success": True},
            "classifications": ["tool_use"],
        },
    )

    metrics = collect_context_metrics(runs)
    item = metrics["by_item"][0]

    assert metrics["observed_runs"] == 3
    assert metrics["call_rate"] == round(2 / 3, 3)
    assert metrics["hit_rate"] == 0.5
    assert metrics["adoption_rate"] == 0.5
    assert item["context_id"] == "docs/contexts/catalog.md"
    assert item["call_rate"] == round(2 / 3, 3)
    assert item["hit_rate"] == 0.5
    assert item["adoption_rate"] == 0.5
    assert item["hit_mode"] == "true_hit"


def test_context_metrics_falls_back_to_run_level_adoption_rate(tmp_path):
    runs = tmp_path / "runs"
    first = write_run(
        runs,
        "baseline",
        "task",
        "first",
        adoption={"ai_generated_lines": None, "accepted_lines": None, "adoption_rate": 0.4},
    )
    second = write_run(
        runs,
        "baseline",
        "task",
        "second",
        adoption={"ai_generated_lines": None, "accepted_lines": None, "adoption_rate": 0.8},
    )
    append_event(first / "events.jsonl", context_event("project_doc", "README.md"))
    append_event(second / "events.jsonl", context_event("project_doc", "README.md"))

    metrics = collect_context_metrics(runs)

    assert metrics["adoption_rate"] == 0.6
    assert metrics["by_type"][0]["adoption_rate"] == 0.6


def test_context_metrics_marks_legacy_and_mixed_hit_modes(tmp_path):
    runs = tmp_path / "runs"
    legacy = write_run(runs, "baseline", "task", "legacy")
    mixed = write_run(runs, "baseline", "task", "mixed")
    append_event(legacy / "events.jsonl", context_event("web", "WebFetch", legacy=True))
    append_event(mixed / "events.jsonl", context_event("web", "WebFetch"))

    metrics = collect_context_metrics(runs)
    item = metrics["by_item"][0]

    assert metrics["hit_mode"] == "mixed"
    assert item["hit_mode"] == "mixed"
    assert metrics["hit_rate"] == 1.0


def test_context_metrics_keeps_adoption_unknown_when_missing(tmp_path):
    runs = tmp_path / "runs"
    run_dir = write_run(runs, "baseline", "task", "called")
    append_event(run_dir / "events.jsonl", context_event("unknown", "mcp__foo__search"))

    metrics = collect_context_metrics(runs)

    assert metrics["adoption_rate"] is None
    assert metrics["by_item"][0]["adoption_rate"] is None
