#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    "scoring",
}

OBSOLETE_TASK_KEYS = {"difficulty"}
EFFORT_SIZES = {"small", "medium", "large"}
BUSINESS_COMPLEXITIES = {"L1_standardized", "L2_linked", "L3_complex"}
CONTEXT_MATURITIES = {"C1_complete", "C2_partial", "C3_missing"}

REQUIRED_SCORING_KEYS = {
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_task_dir(task_dir: Path) -> list[str]:
    errors: list[str] = []
    task_json = task_dir / "task.json"

    for filename in ("task.json", "task.md", "acceptance.md", "tests.sh"):
        if not (task_dir / filename).exists():
            errors.append(f"missing {task_dir / filename}")

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

    scoring = task.get("scoring", {})
    missing_scoring = sorted(REQUIRED_SCORING_KEYS - set(scoring))
    if missing_scoring:
        errors.append(f"{task_json}: missing scoring keys: {', '.join(missing_scoring)}")

    total = sum(float(scoring.get(key, 0)) for key in REQUIRED_SCORING_KEYS)
    if round(total, 5) != 100:
        errors.append(f"{task_json}: scoring weights must sum to 100, got {total:g}")

    if task.get("id") != task_dir.name:
        errors.append(f"{task_json}: id must match directory name {task_dir.name}")

    target = task.get("target")
    if target is not None:
        missing_target = sorted(REQUIRED_TARGET_KEYS - set(target))
        if missing_target:
            errors.append(f"{task_json}: missing target keys: {', '.join(missing_target)}")

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
