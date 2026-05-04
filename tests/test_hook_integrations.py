from __future__ import annotations

import json
from pathlib import Path


def test_codex_hook_templates_are_valid_json_and_reference_adapter():
    hooks = json.loads(Path("integrations/codex/hooks.example.json").read_text(encoding="utf-8"))
    config = Path("integrations/codex/config.example.toml").read_text(encoding="utf-8")

    assert "codex_hooks = true" in config
    assert set(hooks["hooks"]) == {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PermissionRequest",
        "PostToolUse",
        "Stop",
    }
    assert "--adapter codex" in json.dumps(hooks)


def test_claude_hook_template_is_valid_json_and_references_adapter():
    settings = json.loads(Path("integrations/claude-code/settings.example.json").read_text(encoding="utf-8"))

    assert "InstructionsLoaded" in settings["hooks"]
    assert "PostToolUseFailure" in settings["hooks"]
    assert "SessionEnd" in settings["hooks"]
    assert "--adapter claude" in json.dumps(settings)
