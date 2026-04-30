#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_GATE_CAPS = {
    "task_not_solved": 40,
    "security_issue": 50,
    "public_api_break": 55,
    "required_tests_failed": 60,
    "unrelated_changes": 65,
    "hidden_tests_failed": 70,
}

REVIEW_DIMENSIONS = (
    "correctness",
    "regression_safety",
    "maintainability",
    "test_quality",
    "security",
    "process_compliance",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def ratio_score(budget: float | None, actual: float | None) -> float | None:
    if budget is None or actual is None:
        return None
    if budget <= 0:
        return 1.0 if actual == 0 else 0.0
    if actual <= budget:
        return 1.0
    return clamp_unit(budget / actual)


def efficiency_score(task: dict[str, Any], run: dict[str, Any]) -> float:
    candidates = [
        ratio_score(task.get("time_budget_minutes"), run.get("duration_minutes")),
        ratio_score(task.get("max_human_interventions"), run.get("human_interventions")),
        ratio_score(task.get("max_cost_usd"), run.get("cost_usd")),
    ]
    scores = [score for score in candidates if score is not None]
    if not scores:
        return 1.0
    return sum(scores) / len(scores)


def derived_gates(run: dict[str, Any]) -> set[str]:
    gates = set(run.get("hard_gates", []))
    tests = run.get("tests", {})
    diff = run.get("diff", {})
    review = run.get("review", {})

    if tests.get("required_passed") is False:
        gates.add("required_tests_failed")
    if tests.get("hidden_passed") is False:
        gates.add("hidden_tests_failed")
    if diff.get("unrelated_files_changed", 0) > 0:
        gates.add("unrelated_changes")
    if review.get("correctness", 1.0) <= 0:
        gates.add("task_not_solved")
    if review.get("security", 1.0) <= 0:
        gates.add("security_issue")

    return gates


def weighted_score(task: dict[str, Any], run: dict[str, Any]) -> float:
    weights = task["scoring"]
    review = run["review"]

    total_weight = sum(float(weights[key]) for key in weights)
    if total_weight <= 0:
        raise ValueError("scoring weights must sum to a positive number")

    raw = 0.0
    for key in REVIEW_DIMENSIONS:
        raw += float(weights[key]) * clamp_unit(float(review[key]))
    raw += float(weights["efficiency"]) * efficiency_score(task, run)

    return 100.0 * raw / total_weight


def apply_hard_gates(score: float, gates: set[str]) -> float:
    capped = score
    for gate in gates:
        if gate not in DEFAULT_GATE_CAPS:
            raise ValueError(f"unknown hard gate: {gate}")
        capped = min(capped, DEFAULT_GATE_CAPS[gate])
    return capped


def score_run(task: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    gates = derived_gates(run)
    raw_score = weighted_score(task, run)
    final_score = apply_hard_gates(raw_score, gates)
    interventions = max(1, int(run.get("human_interventions", 0)))

    return {
        "raw_score": round(raw_score, 2),
        "score": round(final_score, 2),
        "hard_gates": sorted(gates),
        "attention_adjusted_score": round(final_score / interventions, 2),
        "efficiency": round(efficiency_score(task, run), 3),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score one AI coding workflow run.")
    parser.add_argument("--task", required=True, type=Path, help="Path to task.json")
    parser.add_argument("--run", required=True, type=Path, help="Path to metrics.json")
    parser.add_argument("--write", action="store_true", help="Write score fields back to metrics.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task = load_json(args.task)
    run = load_json(args.run)
    result = score_run(task, run)

    if args.write:
        run.update(result)
        write_json(args.run, run)

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
