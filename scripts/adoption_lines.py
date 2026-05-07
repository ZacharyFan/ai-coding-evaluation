#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_command(["git", *args], repo)


def resolve_worktree(worktree: str) -> Path:
    path = Path(worktree).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"prepared target worktree does not exist: {path}")
    if not (path / ".git").exists():
        raise RuntimeError(f"prepared target worktree must be a git repository: {path}")
    return path


def resolve_commit(repo: Path, ref: str, label: str) -> str:
    result = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if result.returncode != 0:
        message = (
            result.stderr.strip() or result.stdout.strip() or f"failed to resolve {label}: {ref}"
        )
        raise RuntimeError(message)
    return result.stdout.strip()


def task_path_for_run(run_path: Path, task_id: str) -> Path | None:
    candidates = []
    for parent in [run_path.parent, *run_path.parents]:
        candidates.append(parent / "benchmarks" / "tasks" / task_id / "task.json")
    candidates.append(ROOT / "benchmarks" / "tasks" / task_id / "task.json")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def allowed_paths_for_run(run_path: Path, task_id: str) -> list[str] | None:
    task_path = task_path_for_run(run_path, task_id)
    if not task_path:
        return None
    task = load_json(task_path)
    scope = task.get("scope")
    if not isinstance(scope, dict):
        return None
    allowed_paths = scope.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not all(
        isinstance(path, str) for path in allowed_paths
    ):
        return None
    return allowed_paths


def normalize_diff_path(path: str) -> str:
    value = path.strip()
    if value == "/dev/null":
        return value
    if value.startswith("a/") or value.startswith("b/"):
        return value[2:]
    return value


def matches_allowed_path(path: str, allowed_paths: list[str] | None) -> bool:
    if allowed_paths is None:
        return True
    normalized = path.replace("\\", "/")
    for pattern in allowed_paths:
        normalized_pattern = pattern.replace("\\", "/")
        if normalized == normalized_pattern or fnmatch.fnmatchcase(normalized, normalized_pattern):
            return True
    return False


def added_lines_by_file(
    patch: str, allowed_paths: list[str] | None = None
) -> dict[str, Counter[str]]:
    lines: dict[str, Counter[str]] = defaultdict(Counter)
    current_file: str | None = None
    in_hunk = False

    for raw_line in patch.splitlines():
        if raw_line.startswith("diff --git "):
            current_file = None
            in_hunk = False
            continue
        if raw_line.startswith("Binary files ") or raw_line.startswith("GIT binary patch"):
            current_file = None
            in_hunk = False
            continue
        if raw_line.startswith("+++ "):
            current_file = normalize_diff_path(raw_line[4:])
            if current_file == "/dev/null" or not matches_allowed_path(current_file, allowed_paths):
                current_file = None
            in_hunk = False
            continue
        if raw_line.startswith("@@ "):
            in_hunk = True
            continue
        if not in_hunk or current_file is None:
            continue
        if raw_line.startswith("+"):
            lines[current_file][raw_line[1:]] += 1

    return dict(lines)


def diff_added_lines(
    repo: Path, base_ref: str, target_ref: str, allowed_paths: list[str] | None
) -> dict[str, Counter[str]]:
    result = git(repo, "diff", "--unified=0", base_ref, target_ref)
    if result.returncode != 0:
        message = (
            result.stderr.strip()
            or result.stdout.strip()
            or f"failed to diff {base_ref}..{target_ref}"
        )
        raise RuntimeError(message)
    return added_lines_by_file(result.stdout, allowed_paths)


def line_count(lines_by_file: dict[str, Counter[str]]) -> int:
    return sum(sum(counter.values()) for counter in lines_by_file.values())


def intersection_count(left: dict[str, Counter[str]], right: dict[str, Counter[str]]) -> int:
    total = 0
    for path, left_counter in left.items():
        right_counter = right.get(path, Counter())
        total += sum((left_counter & right_counter).values())
    return total


def required_ref(run: dict[str, Any], key: str, cli_value: str | None) -> str:
    value = cli_value
    if value is None:
        adoption = run.get("adoption", {})
        if isinstance(adoption, dict):
            stored = adoption.get(key)
            if isinstance(stored, str) and stored.strip():
                value = stored
    if not value:
        raise ValueError(
            "Fill run.json.adoption.candidate_ref and accepted_ref, "
            "or pass --candidate-ref / --accepted-ref."
        )
    return value


def calculate_adoption(
    run_path: Path,
    *,
    candidate_ref: str | None = None,
    accepted_ref: str | None = None,
    write: bool = False,
) -> dict[str, Any]:
    run = load_json(run_path)
    target = run.get("target", {})
    worktree = target.get("worktree")
    base_ref = target.get("base_ref")
    if not isinstance(worktree, str) or not worktree:
        raise ValueError(
            "run.target.worktree is not set. Run `python -m scripts.prepare_run` first."
        )
    if not isinstance(base_ref, str) or not base_ref:
        raise ValueError("run.target.base_ref is not set.")

    repo = resolve_worktree(worktree)
    resolved_base = resolve_commit(repo, base_ref, "base_ref")
    resolved_candidate = resolve_commit(
        repo, required_ref(run, "candidate_ref", candidate_ref), "candidate_ref"
    )
    resolved_accepted = resolve_commit(
        repo, required_ref(run, "accepted_ref", accepted_ref), "accepted_ref"
    )
    allowed_paths = allowed_paths_for_run(run_path, str(run.get("task_id") or ""))

    candidate_lines = diff_added_lines(repo, resolved_base, resolved_candidate, allowed_paths)
    accepted_lines = diff_added_lines(repo, resolved_base, resolved_accepted, allowed_paths)
    generated = line_count(candidate_lines)
    accepted = intersection_count(candidate_lines, accepted_lines)
    adoption_rate = round(accepted / generated, 3) if generated else None

    adoption = dict(run.get("adoption", {}))
    adoption.update(
        {
            "candidate_ref": resolved_candidate,
            "accepted_ref": resolved_accepted,
            "ai_generated_lines": generated,
            "accepted_lines": accepted,
            "adoption_rate": adoption_rate,
        }
    )
    result = {**run, "adoption": adoption}

    if write:
        write_json(run_path, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate line-level adoption from candidate and accepted commits."
    )
    parser.add_argument("--run", required=True, type=Path, help="Path to run.json")
    parser.add_argument(
        "--candidate-ref",
        default=None,
        help="AI candidate commit/ref. Defaults to run.json adoption field.",
    )
    parser.add_argument(
        "--accepted-ref",
        default=None,
        help="Final accepted commit/ref. Defaults to run.json adoption field.",
    )
    parser.add_argument(
        "--write", action="store_true", help="Write adoption fields back to run.json"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = calculate_adoption(
        args.run,
        candidate_ref=args.candidate_ref,
        accepted_ref=args.accepted_ref,
        write=args.write,
    )
    print(json.dumps(result["adoption"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
