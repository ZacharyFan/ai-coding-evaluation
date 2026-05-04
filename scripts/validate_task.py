#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


REQUIRED_TASK_KEYS = {
    "id",
    "type",
    "effort_size",
    "complexity",
    "time_budget_minutes",
    "required_tests",
    "hidden_checks",
    "scoring_weights",
}

OBSOLETE_TASK_KEYS = {"difficulty", "scoring"}
EFFORT_SIZES = {"small", "medium", "large"}
BUSINESS_COMPLEXITIES = {"L1_standardized", "L2_linked", "L3_complex"}
CONTEXT_MATURITIES = {"C1_complete", "C2_partial", "C3_missing"}

REQUIRED_SCORING_WEIGHT_KEYS = {
    "correctness",
    "regression_safety",
    "maintainability",
    "test_quality",
    "security",
    "process_compliance",
    "efficiency",
}

REQUIRED_TARGET_KEYS = {
    "repo",
    "base_ref",
    "language",
    "test_commands",
}

FULL_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
GIT_SSH_PATTERN = re.compile(r"^[^@\s]+@[^:\s]+:.+")
REMOTE_GIT_PREFIXES = ("http://", "https://", "ssh://", "git://")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_cloneable_git_url(repo: str) -> bool:
    return repo.startswith(REMOTE_GIT_PREFIXES) or GIT_SSH_PATTERN.match(repo) is not None


def is_full_commit_sha(ref: str) -> bool:
    return FULL_SHA_PATTERN.match(ref) is not None


def is_repo_relative_scope_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return not (
        normalized.startswith("/")
        or normalized == ".."
        or normalized.startswith("../")
        or "/../" in normalized
        or normalized.endswith("/..")
    )


def is_official_task_dir(task_dir: Path) -> bool:
    parts = task_dir.parts
    return "benchmarks" in parts and "tasks" in parts


def is_template_task_dir(task_dir: Path) -> bool:
    parts = task_dir.parts
    return "benchmarks" in parts and "templates" in parts


def validate_task_dir(task_dir: Path) -> list[str]:
    errors: list[str] = []
    task_json = task_dir / "task.json"

    for filename in ("task.json", "task.md", "acceptance.md", "tests.sh"):
        if not (task_dir / filename).exists():
            errors.append(f"missing {task_dir / filename}")

    tests_sh = task_dir / "tests.sh"
    if tests_sh.exists() and not os.access(tests_sh, os.X_OK):
        errors.append(f"{tests_sh}: tests.sh must be executable")

    if not task_json.exists():
        return errors

    task = load_json(task_json)
    missing = sorted(REQUIRED_TASK_KEYS - set(task))
    if missing:
        errors.append(f"{task_json}: missing keys: {', '.join(missing)}")

    obsolete = sorted(OBSOLETE_TASK_KEYS & set(task))
    if obsolete:
        errors.append(f"{task_json}: obsolete keys: {', '.join(obsolete)}")

    if task.get("effort_size") not in EFFORT_SIZES:
        errors.append(f"{task_json}: effort_size must be one of: {', '.join(sorted(EFFORT_SIZES))}")

    complexity = task.get("complexity", {})
    if not isinstance(complexity, dict):
        errors.append(f"{task_json}: complexity must be an object")
        complexity = {}

    missing_complexity = sorted({"business_complexity", "context_maturity"} - set(complexity))
    if missing_complexity:
        errors.append(f"{task_json}: missing complexity keys: {', '.join(missing_complexity)}")

    if complexity.get("business_complexity") not in BUSINESS_COMPLEXITIES:
        errors.append(
            f"{task_json}: complexity.business_complexity must be one of: "
            f"{', '.join(sorted(BUSINESS_COMPLEXITIES))}"
        )

    if complexity.get("context_maturity") not in CONTEXT_MATURITIES:
        errors.append(
            f"{task_json}: complexity.context_maturity must be one of: "
            f"{', '.join(sorted(CONTEXT_MATURITIES))}"
        )

    scoring_weights = task.get("scoring_weights", {})
    if not isinstance(scoring_weights, dict):
        errors.append(f"{task_json}: scoring_weights must be an object")
        scoring_weights = {}

    missing_scoring_weights = sorted(REQUIRED_SCORING_WEIGHT_KEYS - set(scoring_weights))
    if missing_scoring_weights:
        errors.append(f"{task_json}: missing scoring_weights keys: {', '.join(missing_scoring_weights)}")

    total = sum(float(scoring_weights.get(key, 0)) for key in REQUIRED_SCORING_WEIGHT_KEYS)
    if round(total, 5) != 100:
        errors.append(f"{task_json}: scoring_weights must sum to 100, got {total:g}")

    if task.get("id") != task_dir.name:
        errors.append(f"{task_json}: id must match directory name {task_dir.name}")

    scope = task.get("scope")
    if scope is not None:
        if not isinstance(scope, dict):
            errors.append(f"{task_json}: scope must be an object")
            scope = {}

        allowed_paths = scope.get("allowed_paths")
        if not isinstance(allowed_paths, list) or not allowed_paths:
            errors.append(f"{task_json}: scope.allowed_paths must be a non-empty list")
            allowed_paths = []

        if not all(isinstance(path, str) and path.strip() for path in allowed_paths):
            errors.append(f"{task_json}: scope.allowed_paths must contain only non-empty strings")

        if any(isinstance(path, str) and not is_repo_relative_scope_path(path) for path in allowed_paths):
            errors.append(f"{task_json}: scope.allowed_paths must be repo-relative paths")

    target = task.get("target")
    if target is not None:
        missing_target = sorted(REQUIRED_TARGET_KEYS - set(target))
        if missing_target:
            errors.append(f"{task_json}: missing target keys: {', '.join(missing_target)}")

        repo = target.get("repo", "")
        base_ref = target.get("base_ref", "")
        solution_ref = target.get("solution_ref")
        if is_official_task_dir(task_dir) and not is_template_task_dir(task_dir):
            if not isinstance(repo, str) or not is_cloneable_git_url(repo):
                errors.append(f"{task_json}: official tasks must use a cloneable Git URL in target.repo")

            if not isinstance(base_ref, str) or not is_full_commit_sha(base_ref):
                errors.append(f"{task_json}: official tasks must pin target.base_ref to a full commit SHA")

            if solution_ref is not None and (not isinstance(solution_ref, str) or not is_full_commit_sha(solution_ref)):
                errors.append(
                    f"{task_json}: official tasks must pin target.solution_ref to a full commit SHA when present"
                )

        if not isinstance(target.get("test_commands", []), list) or not target.get("test_commands"):
            errors.append(f"{task_json}: target.test_commands must be a non-empty list")

        setup_commands = target.get("setup_commands", [])
        if setup_commands and not isinstance(setup_commands, list):
            errors.append(f"{task_json}: target.setup_commands must be a list when present")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate benchmark task directories.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("benchmarks/tasks")],
        help="Task directories or a root containing task directories",
    )
    return parser.parse_args()


def expand_task_dirs(paths: list[Path]) -> list[Path]:
    task_dirs: list[Path] = []
    for path in paths:
        if (path / "task.json").exists():
            task_dirs.append(path)
        else:
            task_dirs.extend(sorted(child for child in path.iterdir() if child.is_dir()))
    return task_dirs


def main() -> None:
    args = parse_args()
    errors: list[str] = []
    for task_dir in expand_task_dirs(args.paths):
        errors.extend(validate_task_dir(task_dir))

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    print("Task validation passed.")


if __name__ == "__main__":
    main()
