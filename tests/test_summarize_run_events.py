from __future__ import annotations

import json
from pathlib import Path

from scripts.summarize_run_events import summarize_run_events


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def base_run() -> dict:
    return {
        "workflow_id": "baseline",
        "task_id": "example-task",
        "model": None,
        "duration_minutes": 0,
        "human_interventions": 0,
        "cost_usd": None,
        "tests": {"required_passed": False, "hidden_passed": None},
        "diff": {"files_changed": 0, "unrelated_files_changed": 0, "scope_check": "not_configured"},
        "process_evidence": {
            "project_instructions_read": False,
            "relevant_docs_read": [],
            "knowledge_sources_used": [],
            "tools_used": [],
            "plan_followed": False,
            "self_review_performed": False,
        },
        "adoption": {
            "ai_generated_lines": None,
            "accepted_lines": None,
            "adoption_rate": None,
        },
        "context_metrics": {
            "call_rate": None,
            "hit_rate": None,
            "adoption_rate": None,
        },
    }


def event(
    hook_event: str,
    *,
    source: str = "codex",
    model: str = "gpt-5.5",
    tool_name: str | None = None,
    command_summary: str = "",
    paths: list[str] | None = None,
    classifications: list[str] | None = None,
    success: bool | None = True,
) -> dict:
    return {
        "schema_version": "1",
        "timestamp": "2026-05-02T00:00:00Z",
        "source": source,
        "session_id": "s1",
        "turn_id": "t1",
        "hook_event": hook_event,
        "model": model,
        "cwd": "/tmp/project",
        "tool_name": tool_name,
        "action": {
            "kind": "tool",
            "command_summary": command_summary,
            "paths": paths or [],
            "success": success,
        },
        "classifications": classifications or [],
    }


def test_summarizes_docs_tools_self_review_and_context_metrics(tmp_path):
    run_path = tmp_path / "run.json"
    events_path = tmp_path / "events.jsonl"
    write_json(run_path, base_run())
    append_event(
        events_path,
        event(
            "PostToolUse",
            tool_name="Read",
            paths=["AGENTS.md"],
            classifications=["tool_use", "read_docs"],
        ),
    )
    append_event(
        events_path,
        event(
            "PostToolUse",
            tool_name="apply_patch",
            command_summary="apply_patch",
            paths=["main.go"],
            classifications=["tool_use", "code_edit"],
        ),
    )
    append_event(
        events_path,
        event(
            "PostToolUse",
            tool_name="Bash",
            command_summary="go test ./...",
            classifications=["tool_use", "test_run"],
        ),
    )
    append_event(
        events_path,
        event(
            "PostToolUse",
            tool_name="WebFetch",
            command_summary="WebFetch",
            classifications=["tool_use", "web_context"],
        ),
    )

    updated = summarize_run_events(run_path, write=True)

    assert updated["model"] == "gpt-5.5"
    assert updated["models_used"] == ["gpt-5.5"]
    assert updated["process_evidence"]["project_instructions_read"] is True
    assert updated["process_evidence"]["relevant_docs_read"] == ["AGENTS.md"]
    assert updated["process_evidence"]["tools_used"] == ["Read", "apply_patch", "go test ./...", "WebFetch"]
    assert updated["process_evidence"]["knowledge_sources_used"] == ["WebFetch"]
    assert updated["process_evidence"]["self_review_performed"] is True
    assert updated["context_metrics"]["call_rate"] == 0.5
    assert updated["context_metrics"]["hit_rate"] == 1.0
    assert updated["event_collection"]["event_count"] == 4
    assert json.loads(run_path.read_text(encoding="utf-8"))["event_collection"]["sources"] == ["codex"]


def test_human_interventions_count_excludes_initial_prompt(tmp_path):
    run_path = tmp_path / "run.json"
    events_path = tmp_path / "events.jsonl"
    write_json(run_path, base_run())
    append_event(events_path, event("UserPromptSubmit", classifications=["user_prompt"]))
    append_event(events_path, event("UserPromptSubmit", classifications=["user_prompt"]))
    append_event(events_path, event("PermissionRequest", classifications=["permission_request"]))

    updated = summarize_run_events(run_path)

    assert updated["human_interventions"] == 1
    assert updated["permission_requests"] == 1


def test_no_events_does_not_pollute_run(tmp_path):
    run_path = tmp_path / "run.json"
    write_json(run_path, base_run())
    before = json.loads(run_path.read_text(encoding="utf-8"))

    updated = summarize_run_events(run_path, write=True)

    assert updated == before
    assert json.loads(run_path.read_text(encoding="utf-8")) == before
