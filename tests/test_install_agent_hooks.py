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

    with pytest.raises(FileExistsError, match="Pass --force"):
        install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex")

    install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex", force=True)
    assert "--adapter codex" in hooks.read_text(encoding="utf-8")


def test_tracked_target_hook_file_is_never_modified(tmp_path):
    target = init_target_repo(tmp_path)
    hooks = target / ".codex" / "hooks.json"
    hooks.parent.mkdir()
    hooks.write_text("{}\n", encoding="utf-8")
    run_git(target, "add", ".codex/hooks.json")
    run_git(target, "commit", "-m", "test: track codex hooks")

    with pytest.raises(RuntimeError, match="refusing to modify tracked target hook config"):
        install_agent_hooks(repo=REPO_ROOT, target=target, agent="codex", force=True)

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
