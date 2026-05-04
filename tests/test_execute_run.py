from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.execute_run import execute_run, load_json


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_target_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "target"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    (repo / "value.txt").write_text("red\n", encoding="utf-8")
    run_git(repo, "add", "value.txt")
    run_git(repo, "commit", "-m", "test: add red baseline")
    return repo, run_git(repo, "rev-parse", "HEAD")


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def write_task_and_run(
    tmp_path: Path,
    repo: Path,
    base_ref: str,
    test_command: str,
    *,
    scope: dict | None = None,
) -> tuple[Path, Path]:
    task = {
        "id": "example-task",
        "time_budget_minutes": 10,
        "max_human_interventions": 2,
        "max_cost_usd": 1.0,
        "target": {
            "repo": str(repo),
            "base_ref": base_ref,
            "language": "text",
            "package_manager": "",
            "setup_commands": [],
            "test_commands": [test_command],
            "working_directory": ".",
        },
        "scoring_weights": {
            "correctness": 35,
            "regression_safety": 15,
            "maintainability": 15,
            "test_quality": 10,
            "security": 10,
            "process_compliance": 5,
            "efficiency": 10,
        },
    }
    if scope is not None:
        task["scope"] = scope
    run = {
        "workflow_id": "baseline",
        "task_id": "example-task",
        "duration_minutes": 0,
        "human_interventions": 1,
        "cost_usd": 0,
        "tests": {
            "required_passed": False,
            "hidden_passed": None,
        },
        "diff": {
            "files_changed": 0,
            "unrelated_files_changed": None,
            "unrelated_files": None,
            "scope_check": "not_configured",
        },
        "process_evidence": {
            "project_instructions_read": False,
            "relevant_docs_read": [],
            "knowledge_sources_used": [],
            "tools_used": [],
            "plan_followed": False,
            "self_review_performed": False,
        },
    }
    run_dir = tmp_path / "runs" / "baseline" / "example-task" / "demo"
    run_dir.mkdir(parents=True)
    task_path = tmp_path / "task.json"
    run_path = run_dir / "run.json"
    write_json(task_path, task)
    write_json(run_path, run)
    return task_path, run_path


def write_remote_task_and_run_without_worktree(tmp_path: Path, base_ref: str) -> tuple[Path, Path]:
    task_path, run_path = write_task_and_run(
        tmp_path,
        Path("https://github.com/owner/repo.git"),
        base_ref,
        f"{sys.executable} -c \"print('ok')\"",
    )
    task = load_json(task_path)
    task["target"]["repo"] = "https://github.com/owner/repo.git"
    write_json(task_path, task)
    return task_path, run_path


def test_execute_run_collects_passing_test_log_diff_and_run_facts(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    (repo / "value.txt").write_text("green\n", encoding="utf-8")
    command = f"{sys.executable} -c \"from pathlib import Path; assert Path('value.txt').read_text() == 'green\\\\n'\""
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, command)

    result = execute_run(task_path, run_path, write=True)

    run_dir = run_path.parent
    run = load_json(run_path)
    assert result["tests"]["required_passed"] is True
    assert run["tests"] == {"required_passed": True, "hidden_passed": None}
    assert run["diff"]["files_changed"] == 1
    assert run["diff"]["scope_check"] == "not_configured"
    assert run["diff"]["unrelated_files_changed"] is None
    assert run["diff"]["unrelated_files"] is None
    assert "review" not in run
    assert "score" not in run
    assert not (run_dir / "score.json").exists()
    assert "value.txt" in (run_dir / "diff.patch").read_text(encoding="utf-8")
    assert "$ " in (run_dir / "test.log").read_text(encoding="utf-8")


def test_execute_run_summarizes_hook_events_when_present(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    (repo / "value.txt").write_text("green\n", encoding="utf-8")
    command = f"{sys.executable} -c \"from pathlib import Path; assert Path('value.txt').read_text() == 'green\\\\n'\""
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, command)
    append_event(
        run_path.parent / "events.jsonl",
        {
            "schema_version": "1",
            "timestamp": "2026-05-02T00:00:00Z",
            "source": "codex",
            "session_id": "s1",
            "turn_id": "t1",
            "hook_event": "PostToolUse",
            "model": "gpt-5.5",
            "cwd": str(repo),
            "tool_name": "Read",
            "action": {
                "kind": "read",
                "command_summary": "Read",
                "paths": ["AGENTS.md"],
                "success": True,
            },
            "classifications": ["tool_use", "read_docs"],
        },
    )

    execute_run(task_path, run_path, write=True)

    run = load_json(run_path)
    assert run["model"] == "gpt-5.5"
    assert run["process_evidence"]["project_instructions_read"] is True
    assert run["event_collection"]["event_count"] == 1


def test_execute_run_uses_prepared_worktree_from_run_json(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    (repo / "value.txt").write_text("green\n", encoding="utf-8")
    command = f"{sys.executable} -c \"from pathlib import Path; assert Path('value.txt').read_text() == 'green\\\\n'\""
    task_path, run_path = write_task_and_run(tmp_path, tmp_path / "missing-local-path", base_ref, command)
    run = load_json(run_path)
    run["target"] = {
        "repo": "https://github.com/owner/repo.git",
        "base_ref": base_ref,
        "worktree": str(repo),
        "language": "text",
        "package_manager": "",
        "working_directory": ".",
    }
    write_json(run_path, run)

    result = execute_run(task_path, run_path, write=True)

    assert result["tests"]["required_passed"] is True
    assert load_json(run_path)["diff"]["files_changed"] == 1


def test_execute_run_applies_scope_allowlist(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    (repo / "value.txt").write_text("green\n", encoding="utf-8")
    (repo / "notes.md").write_text("unrelated\n", encoding="utf-8")
    command = f"{sys.executable} -c \"print('ok')\""
    task_path, run_path = write_task_and_run(
        tmp_path,
        repo,
        base_ref,
        command,
        scope={"allowed_paths": ["value.txt"]},
    )

    result = execute_run(task_path, run_path, write=True)

    run = load_json(run_path)
    assert result["diff"]["files_changed"] == 2
    assert run["diff"]["scope_check"] == "path_allowlist"
    assert run["diff"]["unrelated_files_changed"] == 1
    assert run["diff"]["unrelated_files"] == ["notes.md"]
    assert "notes.md" in (run_path.parent / "diff.patch").read_text(encoding="utf-8")


def test_execute_run_scope_allowlist_supports_globs(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    (repo / "cart").mkdir()
    (repo / "cart" / "cart.go").write_text("package cart\n", encoding="utf-8")
    command = f"{sys.executable} -c \"print('ok')\""
    task_path, run_path = write_task_and_run(
        tmp_path,
        repo,
        base_ref,
        command,
        scope={"allowed_paths": ["cart/**"]},
    )

    execute_run(task_path, run_path, write=True)

    run = load_json(run_path)
    assert run["diff"]["scope_check"] == "path_allowlist"
    assert run["diff"]["unrelated_files_changed"] == 0
    assert run["diff"]["unrelated_files"] == []


def test_execute_run_requires_prepare_run_for_remote_target_without_worktree(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    task_path, run_path = write_remote_task_and_run_without_worktree(tmp_path, base_ref)

    with pytest.raises(RuntimeError, match="run scripts/prepare_run.py first"):
        execute_run(task_path, run_path)


def test_execute_run_records_failing_test_output(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    command = f"{sys.executable} -c \"raise SystemExit('intentional failure')\""
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, command)

    result = execute_run(task_path, run_path, write=True)

    run = load_json(run_path)
    assert result["tests"]["required_passed"] is False
    assert run["tests"] == {"required_passed": False, "hidden_passed": None}
    assert "intentional failure" in (run_path.parent / "test.log").read_text(encoding="utf-8")


def test_reset_to_base_requires_clean_target_repo(tmp_path):
    repo, base_ref = init_target_repo(tmp_path)
    (repo / "value.txt").write_text("dirty\n", encoding="utf-8")
    command = f"{sys.executable} -c \"print('ok')\""
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, command)

    with pytest.raises(RuntimeError, match="target repo must be clean"):
        execute_run(task_path, run_path, write=False, reset_to_base=True)
