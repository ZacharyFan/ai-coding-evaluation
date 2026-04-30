#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an evidence folder for a benchmark run.")
    parser.add_argument("--workflow", required=True, help="Workflow id, matching workflows/{id}.json")
    parser.add_argument("--task", required=True, help="Task id, matching benchmarks/tasks/{id}")
    parser.add_argument("--run-id", default=None, help="Run id. Defaults to UTC timestamp.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    workflow_path = ROOT / "workflows" / f"{args.workflow}.json"
    task_path = ROOT / "benchmarks" / "tasks" / args.task / "task.json"

    if not workflow_path.exists():
        raise SystemExit(f"missing workflow: {workflow_path}")
    if not task_path.exists():
        raise SystemExit(f"missing task: {task_path}")

    workflow = load_json(workflow_path)
    task = load_json(task_path)
    run_dir = ROOT / "runs" / workflow["id"] / task["id"] / run_id
    latest_dir = ROOT / "runs" / workflow["id"] / task["id"] / "latest"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "workflow_id": workflow["id"],
        "task_id": task["id"],
        "target": {
            "repo": task.get("target", {}).get("repo", ""),
            "base_ref": task.get("target", {}).get("base_ref", ""),
            "language": task.get("target", {}).get("language", ""),
            "package_manager": task.get("target", {}).get("package_manager", ""),
            "working_directory": task.get("target", {}).get("working_directory", ""),
        },
        "model": "",
        "duration_minutes": 0,
        "human_interventions": 0,
        "cost_usd": 0,
        "tests": {
            "required_passed": False,
            "hidden_passed": False
        },
        "diff": {
            "files_changed": 0,
            "unrelated_files_changed": 0
        },
        "review": {
            "correctness": 0,
            "regression_safety": 0,
            "maintainability": 0,
            "test_quality": 0,
            "security": 1,
            "process_compliance": 0
        },
        "process_evidence": {
            "project_instructions_read": False,
            "relevant_docs_read": [],
            "knowledge_sources_used": [],
            "tools_used": [],
            "plan_followed": False,
            "review_performed": False
        },
        "hard_gates": []
    }

    metrics_text = json.dumps(metrics, indent=2, sort_keys=True) + "\n"
    write_text_if_missing(run_dir / "metrics.json", metrics_text)
    write_text_if_missing(latest_dir / "metrics.json", metrics_text)
    write_text_if_missing(run_dir / "transcript.md", "# Transcript\n\n")
    write_text_if_missing(run_dir / "review.md", "# Review\n\n")
    write_text_if_missing(run_dir / "test.log", "")
    write_text_if_missing(run_dir / "diff.patch", "")

    print(run_dir)


if __name__ == "__main__":
    main()
