from __future__ import annotations

import json
from pathlib import Path

from scripts.record_hook_event import handle_hook_event, normalize_hook_event, redact_secrets


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_codex_post_tool_use_writes_standard_event(tmp_path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    monkeypatch.setenv("AI_EVAL_RUN_DIR", str(run_dir))

    output = handle_hook_event(
        {
            "session_id": "s1",
            "turn_id": "t1",
            "hook_event_name": "PostToolUse",
            "model": "gpt-5.5",
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": {"command": "go test ./..."},
            "tool_response": {"exit_code": 0},
        },
        "codex",
    )

    events = read_events(run_dir / "events.jsonl")
    assert output == ""
    assert len(events) == 1
    assert events[0]["source"] == "codex"
    assert events[0]["hook_event"] == "PostToolUse"
    assert events[0]["action"]["kind"] == "shell"
    assert events[0]["action"]["command_summary"] == "go test ./..."
    assert events[0]["action"]["success"] is True
    assert "test_run" in events[0]["classifications"]
    assert "tool_use" in events[0]["classifications"]


def test_claude_read_event_is_normalized_without_file_content(tmp_path):
    event = normalize_hook_event(
        {
            "session_id": "s2",
            "hook_event_name": "PostToolUse",
            "model": "claude-opus",
            "cwd": str(tmp_path),
            "tool_name": "Read",
            "tool_input": {
                "file_path": str(tmp_path / "README.md"),
                "content": "do not persist file contents",
            },
            "tool_response": {"success": True},
        },
        "claude",
    )

    assert event["source"] == "claude"
    assert event["action"]["kind"] == "read"
    assert event["action"]["paths"] == [str(tmp_path / "README.md")]
    assert "read_docs" in event["classifications"]
    assert "do not persist" not in json.dumps(event)


def test_apply_patch_event_keeps_only_patch_paths_not_patch_body():
    event = normalize_hook_event(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "apply_patch",
            "tool_input": {
                "command": """*** Begin Patch
*** Update File: app.go
@@
-secret := \"do not persist patch body\"
+secret := \"still do not persist\"
*** End Patch
"""
            },
        },
        "codex",
    )

    serialized = json.dumps(event)
    assert event["action"]["command_summary"] == "apply_patch"
    assert event["action"]["paths"] == ["app.go"]
    assert "do not persist" not in serialized
    assert "code_edit" in event["classifications"]


def test_no_run_dir_is_noop(monkeypatch):
    monkeypatch.delenv("AI_EVAL_RUN_DIR", raising=False)

    output = handle_hook_event(
        {"hook_event_name": "UserPromptSubmit", "prompt": "secret prompt"},
        "codex",
    )

    assert json.loads(output) == {"continue": True, "suppressOutput": True}


def test_redacts_common_secret_shapes():
    text = "api_key=sk-test token=abc123 Authorization: Bearer jwt.value"

    redacted = redact_secrets(text)

    assert "sk-test" not in redacted
    assert "abc123" not in redacted
    assert "jwt.value" not in redacted
    assert "<redacted>" in redacted


def test_coding_phase_blocks_acceptance_reference_reads(tmp_path, monkeypatch):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    monkeypatch.setenv("AI_EVAL_RUN_DIR", str(run_dir))
    monkeypatch.setenv("AI_EVAL_PHASE", "coding")

    output = handle_hook_event(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "benchmarks/tasks/example/acceptance.md"},
        },
        "codex",
    )

    decision = json.loads(output)
    events = read_events(run_dir / "events.jsonl")
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "acceptance.md" in decision["hookSpecificOutput"]["permissionDecisionReason"]
    assert events[0]["action"]["blocked"] is True
    assert "read_acceptance" in events[0]["classifications"]
