#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RED_BACKGROUND = "\033[41m"
GREEN_BACKGROUND = "\033[42m"
RESET = "\033[0m"
HUNK_HEADER_PATTERN = re.compile(r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_worktree(worktree: str) -> Path:
    path = Path(worktree).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"prepared target worktree does not exist: {path}. Run scripts/prepare_run.py first.")
    if not (path / ".git").exists():
        raise RuntimeError(f"prepared target worktree must be a git repository: {path}")
    return path


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def require_success(result: subprocess.CompletedProcess[str], message: str) -> str:
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{message}: {detail}" if detail else message)
    return result.stdout


def should_color(mode: str) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    if mode == "auto":
        return sys.stdout.isatty()
    raise ValueError("color must be one of: auto, always, never")


def normalize_diff_path(raw_path: str) -> str:
    if raw_path == "/dev/null":
        return raw_path
    if raw_path.startswith("a/") or raw_path.startswith("b/"):
        return raw_path[2:]
    return raw_path


def parse_diff_file_path(line: str) -> str:
    parts = line.split()
    if len(parts) >= 4:
        candidate = normalize_diff_path(parts[3])
        if candidate != "/dev/null":
            return candidate
        return normalize_diff_path(parts[2])
    return "unknown"


def colorize_line(line: str, kind: str, *, enabled: bool) -> str:
    if not enabled:
        return line
    if kind == "-":
        return f"{RED_BACKGROUND}{line}{RESET}"
    if kind == "+":
        return f"{GREEN_BACKGROUND}{line}{RESET}"
    return line


def render_diff_line(line_number: int | None, marker: str, content: str, *, enabled: bool) -> str:
    number = "" if line_number is None else str(line_number)
    rendered = f"{number:>5} {marker:<1} {content}"
    return colorize_line(rendered, marker, enabled=enabled)


def render_file_diff(path: str, body_lines: list[str], *, enabled: bool) -> str:
    rendered: list[str] = []
    file_lines: list[str] = []
    additions = 0
    deletions = 0
    old_line: int | None = None
    new_line: int | None = None

    for line in body_lines:
        hunk = HUNK_HEADER_PATTERN.match(line)
        if hunk:
            old_line = int(hunk.group("old_start"))
            new_line = int(hunk.group("new_start"))
            continue
        if old_line is None or new_line is None:
            continue
        if line.startswith("\\"):
            file_lines.append(f"      {line}")
            continue
        if line.startswith("-"):
            file_lines.append(render_diff_line(old_line, "-", line[1:], enabled=enabled))
            old_line += 1
            deletions += 1
            continue
        if line.startswith("+"):
            file_lines.append(render_diff_line(new_line, "+", line[1:], enabled=enabled))
            new_line += 1
            additions += 1
            continue
        content = line[1:] if line.startswith(" ") else line
        file_lines.append(render_diff_line(new_line, "", content, enabled=enabled))
        old_line += 1
        new_line += 1

    rendered.append(f"• Edited {path} (+{additions} -{deletions})")
    rendered.extend(file_lines or ["      (no displayable changes)"])
    return "\n".join(rendered)


def render_review_diff(patch: str, *, enabled: bool) -> str:
    if not patch.strip():
        return "(no changes)"

    files: list[tuple[str, list[str]]] = []
    current_path: str | None = None
    current_lines: list[str] = []
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            if current_path is not None:
                files.append((current_path, current_lines))
            current_path = parse_diff_file_path(line)
            current_lines = []
            continue
        if current_path is None:
            continue
        if line.startswith(("index ", "similarity index ", "rename from ", "rename to ", "new file mode ", "deleted file mode ", "--- ", "+++ ")):
            continue
        current_lines.append(line)

    if current_path is not None:
        files.append((current_path, current_lines))

    if not files:
        return "(no changes)"
    return "\n\n".join(render_file_diff(path, lines, enabled=enabled) for path, lines in files)


def scoped_diff_args(task: dict[str, Any], solution_ref: str, *, stat: bool = False) -> list[str]:
    args = ["diff", "-R"]
    if stat:
        args.append("--stat")
    args.append(solution_ref)

    scope = task.get("scope")
    if not scope:
        return args

    allowed_paths = scope.get("allowed_paths", [])
    if not isinstance(allowed_paths, list) or not all(isinstance(path, str) and path for path in allowed_paths):
        raise ValueError("task.scope.allowed_paths must be a list of non-empty strings")
    return [*args, "--", *allowed_paths]


def render_scope_note(task: dict[str, Any]) -> str | None:
    scope = task.get("scope")
    if not scope:
        return None
    allowed_paths = scope.get("allowed_paths", [])
    if not allowed_paths:
        return None
    return "Scope: " + ", ".join(f"`{path}`" for path in allowed_paths)


def show_solution_diff(task_path: Path, run_path: Path, *, color: str = "auto") -> str:
    task = load_json(task_path)
    run = load_json(run_path)
    target = task.get("target", {})
    solution_ref = target.get("solution_ref")
    if not solution_ref:
        raise ValueError("target.solution_ref is not set for this task")

    worktree = run.get("target", {}).get("worktree")
    if not worktree:
        raise ValueError("run.target.worktree is not set. Run scripts/prepare_run.py first.")

    repo = resolve_worktree(worktree)
    stat = require_success(
        run_git(repo, *scoped_diff_args(task, solution_ref, stat=True)),
        f"failed to diff --stat candidate worktree..{solution_ref}",
    ).rstrip()
    patch = require_success(
        run_git(repo, *scoped_diff_args(task, solution_ref)),
        f"failed to diff candidate worktree..{solution_ref}",
    ).rstrip()
    rendered_patch = render_review_diff(patch, enabled=should_color(color))
    scope_note = render_scope_note(task)

    sections = [
        f"# Candidate result vs reference solution: candidate worktree..{solution_ref}",
        *([scope_note] if scope_note else []),
        "",
        "## Diff Stat",
        stat or "(no changes)",
        "",
        "## Review Diff",
        rendered_patch,
        "",
    ]
    return "\n".join(sections)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print the candidate-vs-reference solution diff for manual review.")
    parser.add_argument("--task", required=True, type=Path, help="Path to task.json")
    parser.add_argument("--run", required=True, type=Path, help="Path to run.json with target.worktree")
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Color patch additions/deletions with ANSI backgrounds. Defaults to auto.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        print(show_solution_diff(args.task, args.run, color=args.color), end="")
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
