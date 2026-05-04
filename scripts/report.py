#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.report_data import collect_runs, group_by, is_scored, summarize_runs


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def fmt_summary(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "unscored"


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
    print("\n| Workflow | Runs | Avg Score | Avg Attention Score | First Pass Rate |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for workflow, items in sorted(group_by(runs, "workflow_id").items()):
        scored = [item for item in items if is_scored(item)]
        summary = summarize_runs(items)
        if not scored:
            print(f"| {workflow} | {len(items)} | unscored | unscored | unscored |")
            continue
        print(
            f"| {workflow} | {len(items)} | "
            f"{fmt_summary(summary['avg_score'])} | "
            f"{fmt_summary(summary['avg_attention_score'])} | "
            f"{fmt_summary(summary['first_pass_rate'])} |"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a markdown report from run and score files.")
    parser.add_argument("--runs", type=Path, default=Path("runs"), help="Runs root directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = collect_runs(args.runs)
    if not runs:
        print("No run facts found.")
        return
    print_runs(runs)
    print_summary(runs)


if __name__ == "__main__":
    main()
