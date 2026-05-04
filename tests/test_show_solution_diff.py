from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.show_solution_diff import GREEN_BACKGROUND, RED_BACKGROUND, RESET, show_solution_diff


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init_repo_with_solution(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "target"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    (repo / "value.txt").write_text("red\n", encoding="utf-8")
    run_git(repo, "add", "value.txt")
    run_git(repo, "commit", "-m", "test: add baseline")
    base_ref = run_git(repo, "rev-parse", "HEAD")
    (repo / "value.txt").write_text("green\n", encoding="utf-8")
    run_git(repo, "add", "value.txt")
    run_git(repo, "commit", "-m", "fix: add solution")
    solution_ref = run_git(repo, "rev-parse", "HEAD")
    run_git(repo, "checkout", base_ref)
    return repo, base_ref, solution_ref


def write_candidate(repo: Path, content: str) -> None:
    (repo / "value.txt").write_text(content, encoding="utf-8")


def write_task_and_run(
    tmp_path: Path,
    repo: Path,
    base_ref: str,
    solution_ref: str | None,
    *,
    scope: dict | None = None,
) -> tuple[Path, Path]:
    task_path = tmp_path / "task.json"
    run_path = tmp_path / "run.json"
    target = {
        "repo": "https://github.com/owner/repo.git",
        "base_ref": base_ref,
        "language": "text",
        "test_commands": ["test -f value.txt"],
    }
    if solution_ref is not None:
        target["solution_ref"] = solution_ref
    task = {"id": "task", "target": target}
    if scope is not None:
        task["scope"] = scope
    write_json(task_path, task)
    write_json(
        run_path,
        {
            "workflow_id": "baseline",
            "task_id": "task",
            "target": {"worktree": str(repo)},
        },
    )
    return task_path, run_path


def test_show_solution_diff_prints_review_friendly_diff(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    write_candidate(repo, "blue\n")
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, solution_ref)

    output = show_solution_diff(task_path, run_path, color="never")

    assert f"# Candidate result vs reference solution: candidate worktree..{solution_ref}" in output
    assert "## Diff Stat" in output
    assert "value.txt" in output
    assert "## Review Diff" in output
    assert "• Edited value.txt (+1 -1)" in output
    assert "    1 - blue" in output
    assert "    1 + green" in output
    assert "-red" not in output
    assert "diff --git" not in output
    assert "index " not in output
    assert "--- a/" not in output
    assert "+++ b/" not in output


def test_show_solution_diff_has_no_patch_when_candidate_matches_solution(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    write_candidate(repo, "green\n")
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, solution_ref)

    output = show_solution_diff(task_path, run_path, color="never")

    assert "## Diff Stat\n(no changes)" in output
    assert "## Review Diff\n(no changes)" in output


def test_show_solution_diff_respects_task_scope_allowlist(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    write_candidate(repo, "green\n")
    (repo / ".codex").mkdir()
    (repo / ".codex" / "hooks.json").write_text("{}\n", encoding="utf-8")
    run_git(repo, "add", ".codex/hooks.json")
    run_git(repo, "commit", "-m", "test: add out-of-scope file")
    task_path, run_path = write_task_and_run(
        tmp_path,
        repo,
        base_ref,
        solution_ref,
        scope={"allowed_paths": ["value.txt"]},
    )

    output = show_solution_diff(task_path, run_path, color="never")

    assert "Scope: `value.txt`" in output
    assert "## Diff Stat\n(no changes)" in output
    assert ".codex/hooks.json" not in output


def test_show_solution_diff_color_always_highlights_patch_lines_not_file_headers(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    write_candidate(repo, "blue\n")
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, solution_ref)

    output = show_solution_diff(task_path, run_path, color="always")

    assert f"{RED_BACKGROUND}    1 - blue{RESET}" in output
    assert f"{GREEN_BACKGROUND}    1 + green{RESET}" in output
    assert f"{RED_BACKGROUND}--- " not in output
    assert f"{GREEN_BACKGROUND}+++ " not in output


def test_show_solution_diff_color_never_omits_ansi(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    write_candidate(repo, "blue\n")
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, solution_ref)

    output = show_solution_diff(task_path, run_path, color="never")

    assert "\033[" not in output


def test_show_solution_diff_fails_when_solution_ref_is_missing(tmp_path):
    repo, base_ref, _solution_ref = init_repo_with_solution(tmp_path)
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, None)

    with pytest.raises(ValueError, match="target.solution_ref is not set for this task"):
        show_solution_diff(task_path, run_path)


def test_show_solution_diff_fails_without_prepared_worktree(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, solution_ref)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    del run["target"]["worktree"]
    write_json(run_path, run)

    with pytest.raises(ValueError, match="Run scripts/prepare_run.py first"):
        show_solution_diff(task_path, run_path)


def test_show_solution_diff_surfaces_missing_git_ref_error(tmp_path):
    repo, base_ref, _solution_ref = init_repo_with_solution(tmp_path)
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, "0" * 40)

    with pytest.raises(RuntimeError, match="failed to diff --stat candidate worktree"):
        show_solution_diff(task_path, run_path)


def test_show_solution_diff_cli_reports_clean_error_without_traceback(tmp_path):
    repo, base_ref, solution_ref = init_repo_with_solution(tmp_path)
    task_path, run_path = write_task_and_run(tmp_path, repo, base_ref, solution_ref)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["target"]["worktree"] = str(tmp_path / "missing-target")
    write_json(run_path, run)

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "show_solution_diff.py"),
            "--task",
            str(task_path),
            "--run",
            str(run_path),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "error: prepared target worktree does not exist" in result.stderr
    assert "Traceback" not in result.stderr
