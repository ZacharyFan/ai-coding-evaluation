#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def collect_runs(root: Path) -> list[dict[str, Any]]:
    runs = []
    for path in sorted(root.glob("*/*/*/metrics.json")):
        if path.parent.name == "latest":
            continue
        data = load_json(path)
        data["_path"] = str(path)
        runs.append(data)
    return runs


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def print_runs(runs: list[dict[str, Any]]) -> None:
    print("| Workflow | Task | Score | Attention Score | Time | Human | Gates |")
    print("| --- | --- | ---: | ---: | ---: | ---: | --- |")
    for run in runs:
        gates = ", ".join(run.get("hard_gates", [])) or "-"
        print(
            "| "
            + " | ".join(
                [
                    run.get("workflow_id", ""),
                    run.get("task_id", ""),
                    fmt(run.get("score", "unscored")),
                    fmt(run.get("attention_adjusted_score", "unscored")),
                    fmt(run.get("duration_minutes", "")),
                    fmt(run.get("human_interventions", "")),
                    gates,
                ]
            )
            + " |"
        )


def print_summary(runs: list[dict[str, Any]]) -> None:
    by_workflow: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        by_workflow.setdefault(run.get("workflow_id", ""), []).append(run)

    print("\n| Workflow | Runs | Avg Score | Avg Attention Score | First Pass Rate |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for workflow, items in sorted(by_workflow.items()):
        scored = [item for item in items if isinstance(item.get("score"), (int, float))]
        if not scored:
            print(f"| {workflow} | {len(items)} | unscored | unscored | unscored |")
            continue
        first_pass = [
            item
            for item in scored
            if item.get("tests", {}).get("required_passed") is True and not item.get("hard_gates")
        ]
        print(
            f"| {workflow} | {len(items)} | "
            f"{mean(item['score'] for item in scored):.2f} | "
            f"{mean(item.get('attention_adjusted_score', 0) for item in scored):.2f} | "
            f"{len(first_pass) / len(scored):.2f} |"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a markdown report from run metrics.")
    parser.add_argument("--runs", type=Path, default=Path("runs"), help="Runs root directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = collect_runs(args.runs)
    if not runs:
        print("No run metrics found.")
        return
    print_runs(runs)
    print_summary(runs)


if __name__ == "__main__":
    main()
