from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.install_agent_hooks import install_agent_hooks, resolve_repo

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_target_repo(tmp_path: Path) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    run_git(target, "init", "-b", "main")
    run_git(target, "config", "user.email", "test@example.com")
    run_git(target, "config", "user.name", "Test User")
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    run_git(target, "add", "README.md")
    run_git(target, "commit", "-m", "test: init target")
    return target


def test_installs_codex_and_claude_hooks_and_excludes_them(tmp_path):
    target = init_target_repo(tmp_path)

    result = install_agent_hooks(repo=REPO_ROOT, target=target)

    assert result["installed"] == [
        ".codex/config.toml",
        ".codex/hooks.json",
        ".claude/settings.local.json",
    ]
    assert "codex_hooks = true" in (target / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "--adapter codex" in json.dumps(
        json.loads((target / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    )
    assert "--adapter claude" in json.dumps(
        json.loads((target / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
    )
    exclude = (target / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert ".codex/config.toml" in exclude
    assert ".codex/hooks.json" in exclude
    assert ".claude/settings.local.json" in exclude
    assert run_git(target, "status", "--short") == ""


def test_install_is_idempotent_for_same_content(tmp_path):
    target = init_target_repo(tmp_path)

    install_agent_hooks(repo=REPO_ROOT, target=target)
    result = install_agent_hooks(repo=REPO_ROOT, target=target)

    assert result["installed"] == [
        ".codex/config.toml",
        ".codex/hooks.json",
        ".claude/settings.local.json",
    ]


def test_existing_different_untracked_file_requires_force(tmp_path):
    target = init_target_repo(tmp_path)
    hooks = target / ".codex" / "hooks.json"
    hooks.parent.mkdir()
    hooks.write_text("{}\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Pass --merge"):
        install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex")

    install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex", force=True)
    assert "--adapter codex" in hooks.read_text(encoding="utf-8")


def test_merge_preserves_existing_codex_config_and_hooks_without_duplicates(tmp_path):
    target = init_target_repo(tmp_path)
    codex = target / ".codex"
    codex.mkdir()
    (codex / "config.toml").write_text(
        '[features]\nother_feature = true\ncodex_hooks = false\n\n[ui]\ntheme = "dark"\n',
        encoding="utf-8",
    )
    (codex / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "*",
                            "hooks": [{"type": "command", "command": "custom codex hook"}],
                        }
                    ]
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex", merge=True)
    install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex", merge=True)

    config = (codex / "config.toml").read_text(encoding="utf-8")
    hooks = json.loads((codex / "hooks.json").read_text(encoding="utf-8"))
    post_tool_use = hooks["hooks"]["PostToolUse"]
    commands = [
        hook["command"]
        for entry in post_tool_use
        for hook in entry.get("hooks", [])
        if "command" in hook
    ]

    assert "other_feature = true" in config
    assert "codex_hooks = true" in config
    assert "codex_hooks = false" not in config
    assert "[ui]" in config
    assert commands.count("custom codex hook") == 1
    assert (
        commands.count('python "$AI_EVAL_REPO/scripts/record_hook_event.py" --adapter codex') == 1
    )
    assert "SessionStart" in hooks["hooks"]


def test_merge_preserves_existing_claude_hooks_without_duplicates(tmp_path):
    target = init_target_repo(tmp_path)
    claude = target / ".claude"
    claude.mkdir()
    (claude / "settings.local.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "Stop": [
                        {
                            "hooks": [{"type": "command", "command": "custom claude hook"}],
                        }
                    ]
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    install_agent_hooks(repo=REPO_ROOT, target=target, agent="claude", merge=True)
    install_agent_hooks(repo=REPO_ROOT, target=target, agent="claude", merge=True)

    settings = json.loads((claude / "settings.local.json").read_text(encoding="utf-8"))
    stop_commands = [
        hook["command"]
        for entry in settings["hooks"]["Stop"]
        for hook in entry.get("hooks", [])
        if "command" in hook
    ]

    assert stop_commands.count("custom claude hook") == 1
    assert (
        stop_commands.count('python "$AI_EVAL_REPO/scripts/record_hook_event.py" --adapter claude')
        == 1
    )
    assert "InstructionsLoaded" in settings["hooks"]


def test_force_and_merge_are_mutually_exclusive(tmp_path):
    target = init_target_repo(tmp_path)

    with pytest.raises(ValueError, match="mutually exclusive"):
        install_agent_hooks(repo=REPO_ROOT, target=target, force=True, merge=True)


def test_tracked_target_hook_file_is_never_modified(tmp_path):
    target = init_target_repo(tmp_path)
    hooks = target / ".codex" / "hooks.json"
    hooks.parent.mkdir()
    hooks.write_text("{}\n", encoding="utf-8")
    run_git(target, "add", ".codex/hooks.json")
    run_git(target, "commit", "-m", "test: track codex hooks")

    for kwargs in ({"force": True}, {"merge": True}):
        with pytest.raises(RuntimeError, match="refusing to modify tracked target hook config"):
            install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex", **kwargs)

    assert hooks.read_text(encoding="utf-8") == "{}\n"


def test_cli_uses_eval_environment_from_any_cwd(tmp_path):
    target = init_target_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    env = {
        **os.environ,
        "AI_EVAL_REPO": str(REPO_ROOT),
        "AI_EVAL_TARGET_WORKTREE": str(target),
    }

    process = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "install_agent_hooks.py")],
        cwd=outside,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0
    assert "Installed hook files into" in process.stdout
    assert (target / ".codex" / "hooks.json").exists()
    assert (target / ".claude" / "settings.local.json").exists()


def test_resolve_repo_falls_back_to_script_repo(monkeypatch):
    monkeypatch.delenv("AI_EVAL_REPO", raising=False)

    assert resolve_repo(None) == REPO_ROOT
