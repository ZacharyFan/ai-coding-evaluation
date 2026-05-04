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


def review_hint() -> str:
    fields = " ".join(f"{dimension}=<0-1>" for dimension in REVIEW_DIMENSIONS)
    return f"Use --set-review {fields} --write, or run scripts/llm_review_run.py to generate review scores first."


def init_score_doc(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "workflow_id": run.get("workflow_id", ""),
        "task_id": run.get("task_id", ""),
        "review": {dimension: None for dimension in REVIEW_DIMENSIONS},
        "review_sources": {dimension: "manual_pending" for dimension in REVIEW_DIMENSIONS},
        "review_notes": {},
        "manual_hard_gates": [],
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_initialized_score(path: Path, run: dict[str, Any]) -> dict[str, Any]:
    if path.exists():
        raise FileExistsError(f"score file already exists: {path}")
    score = init_score_doc(run)
    write_json(path, score)
    return score


def parse_review_assignment(value: str) -> tuple[str, float]:
    if "=" not in value:
        raise ValueError(f"review assignment must use dimension=value: {value}")
    key, raw_score = value.split("=", 1)
    key = key.strip()
    if key not in REVIEW_DIMENSIONS:
        allowed = ", ".join(REVIEW_DIMENSIONS)
        raise ValueError(f"unknown review dimension: {key}. Allowed dimensions: {allowed}")
    try:
        score = float(raw_score)
    except ValueError as error:
        raise ValueError(f"review.{key} must be a number between 0 and 1") from error
    if score < 0 or score > 1:
        raise ValueError(f"review.{key} must be between 0 and 1")
    return key, score


def apply_manual_review(score: dict[str, Any], assignments: list[str], hard_gates: list[str] | None) -> dict[str, Any]:
    updated = dict(score)
    updated["review"] = dict(updated.get("review", {}))
    updated["review_sources"] = dict(updated.get("review_sources", {}))
    updated.setdefault("review_notes", {})

    for assignment in assignments:
        key, value = parse_review_assignment(assignment)
        updated["review"][key] = value
        updated["review_sources"][key] = "manual"

    if hard_gates is not None:
        unknown = sorted(set(hard_gates) - set(DEFAULT_GATE_CAPS))
        if unknown:
            allowed = ", ".join(sorted(DEFAULT_GATE_CAPS))
            raise ValueError(f"unknown manual hard gate: {unknown[0]}. Allowed gates: {allowed}")
        updated["manual_hard_gates"] = sorted(set(hard_gates))
    else:
        updated.setdefault("manual_hard_gates", [])

    return updated


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


def derived_gates(run: dict[str, Any], score: dict[str, Any]) -> set[str]:
    gates: set[str] = set()
    tests = run.get("tests", {})
    diff = run.get("diff", {})
    review = score.get("review", {})

    if tests.get("required_passed") is False:
        gates.add("required_tests_failed")
    if tests.get("hidden_passed") is False:
        gates.add("hidden_tests_failed")
    unrelated = diff.get("unrelated_files_changed", 0)
    if unrelated is not None and unrelated > 0:
        gates.add("unrelated_changes")
    if review.get("correctness", 1.0) <= 0:
        gates.add("task_not_solved")
    if review.get("security", 1.0) <= 0:
        gates.add("security_issue")

    return gates


def weighted_score(task: dict[str, Any], run: dict[str, Any], score: dict[str, Any]) -> float:
    weights = task["scoring_weights"]
    review = score["review"]

    total_weight = sum(float(weights[key]) for key in weights)
    if total_weight <= 0:
        raise ValueError("scoring_weights must sum to a positive number")

    raw = 0.0
    for key in REVIEW_DIMENSIONS:
        value = review.get(key)
        if value is None:
            raise ValueError(f"review.{key} must be filled before scoring")
        raw += float(weights[key]) * clamp_unit(float(value))
    raw += float(weights["efficiency"]) * efficiency_score(task, run)

    return 100.0 * raw / total_weight


def apply_hard_gates(score: float, gates: set[str]) -> float:
    capped = score
    for gate in gates:
        if gate not in DEFAULT_GATE_CAPS:
            raise ValueError(f"unknown hard gate: {gate}")
        capped = min(capped, DEFAULT_GATE_CAPS[gate])
    return capped


def score_run(task: dict[str, Any], run: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REVIEW_DIMENSIONS if key not in score.get("review", {}) or score["review"][key] is None]
    if missing:
        raise ValueError(
            f"review.{missing[0]} must be filled before scoring; "
            f"missing review fields: {', '.join(missing)}. "
            f"{review_hint()}"
        )
    derived = derived_gates(run, score)
    manual = set(score.get("manual_hard_gates", []))
    gates = manual | derived
    raw_score = weighted_score(task, run, score)
    final_score = apply_hard_gates(raw_score, gates)
    interventions = max(1, int(run.get("human_interventions", 0)))

    return {
        "raw_score": round(raw_score, 2),
        "score": round(final_score, 2),
        "manual_hard_gates": sorted(manual),
        "derived_hard_gates": sorted(derived),
        "hard_gates": sorted(gates),
        "attention_adjusted_score": round(final_score / interventions, 2),
        "efficiency": round(efficiency_score(task, run), 3),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score one AI coding workflow run.")
    parser.add_argument("--task", type=Path, help="Path to task.json")
    parser.add_argument("--run", type=Path, help="Path to run.json. Defaults to score.json sibling run.json.")
    parser.add_argument("--score", required=True, type=Path, help="Path to score.json")
    parser.add_argument("--init", action="store_true", help="Create a manual scoring draft score.json")
    parser.add_argument(
        "--set-review",
        nargs="+",
        metavar="DIMENSION=VALUE",
        help="Set manual review scores, for example correctness=1.0 maintainability=0.8",
    )
    parser.add_argument(
        "--manual-hard-gate",
        action="append",
        dest="manual_hard_gates",
        help="Add a manual hard gate such as public_api_break. Repeat for multiple gates.",
    )
    parser.add_argument("--write", action="store_true", help="Write score fields back to score.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_path = args.run or args.score.parent / "run.json"
    run = load_json(run_path)

    if args.init:
        result = init_score_doc(run)
        if args.write:
            write_initialized_score(args.score, run)
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    if args.task is None:
        raise SystemExit("--task is required unless --init is used. " + review_hint())

    task = load_json(args.task)
    score = load_json(args.score) if args.score.exists() else init_score_doc(run)
    if args.set_review or args.manual_hard_gates is not None:
        score = apply_manual_review(score, args.set_review or [], args.manual_hard_gates)
    result = score_run(task, run, score)

    if args.write:
        score.update(result)
        write_json(args.score, score)

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
