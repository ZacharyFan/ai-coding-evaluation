#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_task import is_cloneable_git_url


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_target_repo(repo: str) -> Path:
    path = Path(repo).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"target repo does not exist: {path}")
    if not (path / ".git").exists():
        raise RuntimeError(f"target repo must be a local git repository: {path}")
    return path


def resolve_prepared_worktree(worktree: str) -> Path:
    path = Path(worktree).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"prepared target worktree does not exist: {path}")
    if not (path / ".git").exists():
        raise RuntimeError(f"prepared target worktree must be a git repository: {path}")
    return path


def resolve_execution_repo(task_target: dict[str, Any], run: dict[str, Any]) -> Path:
    run_target = run.get("target", {})
    worktree = run_target.get("worktree")
    if worktree:
        return resolve_prepared_worktree(worktree)

    repo = task_target["repo"]
    if is_cloneable_git_url(repo):
        raise RuntimeError("remote target repo has no prepared worktree; run scripts/prepare_run.py first")

    return resolve_target_repo(repo)


def run_command(command: list[str] | str, cwd: Path, *, shell: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=shell,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_command(["git", *args], repo)


def ensure_clean_repo(repo: Path) -> None:
    status = git(repo, "status", "--porcelain")
    if status.returncode != 0:
        raise RuntimeError(status.stderr.strip() or "failed to inspect target repo status")
    if status.stdout.strip():
        raise RuntimeError("target repo must be clean before --reset-to-base")


def checkout_base(repo: Path, base_ref: str) -> None:
    ensure_clean_repo(repo)
    checkout = git(repo, "checkout", base_ref)
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr.strip() or f"failed to checkout {base_ref}")


def command_block(command: str, result: subprocess.CompletedProcess[str]) -> str:
    parts = [f"$ {command}", f"exit_code={result.returncode}"]
    if result.stdout:
        parts.extend(["", result.stdout.rstrip()])
    if result.stderr:
        parts.extend(["", result.stderr.rstrip()])
    return "\n".join(parts).rstrip() + "\n"


def run_shell_commands(commands: list[str], cwd: Path) -> tuple[bool, str]:
    blocks: list[str] = []
    passed = True
    for command in commands:
        result = run_command(command, cwd, shell=True)
        blocks.append(command_block(command, result))
        if result.returncode != 0:
            passed = False
            break
    return passed, "\n".join(blocks)


def diff_text(repo: Path, base_ref: str) -> str:
    diff = git(repo, "diff", base_ref)
    if diff.returncode != 0:
        raise RuntimeError(diff.stderr.strip() or f"failed to diff against {base_ref}")
    return diff.stdout


def changed_files(repo: Path, base_ref: str) -> list[str]:
    diff = git(repo, "diff", "--name-only", base_ref)
    if diff.returncode != 0:
        raise RuntimeError(diff.stderr.strip() or f"failed to list changed files against {base_ref}")
    return [line for line in diff.stdout.splitlines() if line.strip()]


def execute_run(
    task_path: Path,
    run_path: Path,
    *,
    write: bool = False,
    reset_to_base: bool = False,
    expect_fail: bool = False,
) -> dict[str, Any]:
    task = load_json(task_path)
    run = load_json(run_path)
    target = task["target"]
    target_repo = resolve_execution_repo(target, run)
    working_directory = target_repo / target.get("working_directory", ".")
    base_ref = target["base_ref"]
    run_dir = run_path.parent

    if reset_to_base:
        checkout_base(target_repo, base_ref)

    commands = list(target.get("setup_commands", [])) + list(target.get("test_commands", []))
    started = time.monotonic()
    required_passed, test_output = run_shell_commands(commands, working_directory)
    duration_minutes = round((time.monotonic() - started) / 60, 3)

    diff = diff_text(target_repo, base_ref)
    files_changed = len(changed_files(target_repo, base_ref))

    result = {
        "duration_minutes": duration_minutes,
        "tests": {
            "required_passed": required_passed,
            "hidden_passed": run.get("tests", {}).get("hidden_passed"),
        },
        "diff": {
            "files_changed": files_changed,
            "unrelated_files_changed": run.get("diff", {}).get("unrelated_files_changed", 0),
            "scope_check": run.get("diff", {}).get("scope_check", "not_configured"),
        },
    }

    updated_run = {**run, **result}

    if write:
        (run_dir / "test.log").write_text(test_output, encoding="utf-8")
        (run_dir / "diff.patch").write_text(diff, encoding="utf-8")
        write_json(run_path, updated_run)

    if expect_fail and required_passed:
        raise RuntimeError("expected required tests to fail, but they passed")

    return updated_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute target checks and collect run evidence.")
    parser.add_argument("--task", required=True, type=Path, help="Path to task.json")
    parser.add_argument("--run", required=True, type=Path, help="Path to run.json")
    parser.add_argument("--write", action="store_true", help="Write test.log, diff.patch, and run.json")
    parser.add_argument("--reset-to-base", action="store_true", help="Checkout target.base_ref before running commands")
    parser.add_argument("--expect-fail", action="store_true", help="Treat failing required tests as expected")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = execute_run(
        args.task,
        args.run,
        write=args.write,
        reset_to_base=args.reset_to_base,
        expect_fail=args.expect_fail,
    )
    print(json.dumps(result, indent=2, sort_keys=True))

    if not args.expect_fail and result["tests"]["required_passed"] is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
