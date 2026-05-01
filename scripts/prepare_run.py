#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WORKFLOW_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

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


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_command(["git", *args], cwd)


def ensure_success(result: subprocess.CompletedProcess[str], fallback: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or fallback)


def validate_workflow_id(workflow_id: str) -> str:
    if not WORKFLOW_ID_PATTERN.fullmatch(workflow_id) or ".." in workflow_id:
        raise ValueError("workflow_id must use only A-Z, a-z, 0-9, '.', '_', '-' and must not contain '..'")
    return workflow_id


def initial_run(workflow_id: str, task: dict[str, Any], target_dir: Path) -> dict[str, Any]:
    target = task.get("target", {})
    return {
        "workflow_id": workflow_id,
        "task_id": task["id"],
        "target": {
            "repo": target.get("repo", ""),
            "base_ref": target.get("base_ref", ""),
            "worktree": str(target_dir),
            "language": target.get("language", ""),
            "package_manager": target.get("package_manager", ""),
            "working_directory": target.get("working_directory", "."),
        },
        "model": "",
        "duration_minutes": 0,
        "human_interventions": 0,
        "cost_usd": 0,
        "tests": {
            "required_passed": False,
            "hidden_passed": None,
        },
        "diff": {
            "files_changed": 0,
            "unrelated_files_changed": 0,
            "scope_check": "not_configured",
        },
        "process_evidence": {
            "project_instructions_read": False,
            "relevant_docs_read": [],
            "knowledge_sources_used": [],
            "tools_used": [],
            "plan_followed": False,
            "self_review_performed": False,
        },
    }


def transcript_template(workflow_id: str, task_id: str, run_id: str, target_dir: Path) -> str:
    return f"""# Transcript

Run target worktree prepared by `scripts/prepare_run.py`.

```text
workflow  {workflow_id}
task      {task_id}
run_id    {run_id}
target    {target_dir}
```

Fill this after the workflow runs. Include the key prompts, decisions, tool usage, human interventions, and anything a reviewer needs to reconstruct the run.
"""


def prepare_run(root: Path, workflow_id: str, task_id: str, run_id: str | None = None) -> Path:
    workflow_id = validate_workflow_id(workflow_id)
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    task_path = root / "benchmarks" / "tasks" / task_id / "task.json"

    if not task_path.exists():
        raise FileNotFoundError(f"missing task: {task_path}")

    task = load_json(task_path)
    run_dir = root / "runs" / workflow_id / task["id"] / run_id
    target_dir = run_dir / "target"

    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")

    run_dir.mkdir(parents=True)
    target = task["target"]
    clone = git(root, "clone", target["repo"], str(target_dir))
    ensure_success(clone, f"failed to clone {target['repo']}")

    checkout = git(target_dir, "checkout", target["base_ref"])
    ensure_success(checkout, f"failed to checkout {target['base_ref']}")

    write_json(run_dir / "run.json", initial_run(workflow_id, task, target_dir))
    (run_dir / "transcript.md").write_text(
        transcript_template(workflow_id, task["id"], run_id, target_dir),
        encoding="utf-8",
    )
    (run_dir / "test.log").write_text("", encoding="utf-8")
    (run_dir / "diff.patch").write_text("", encoding="utf-8")
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare an isolated target worktree for a benchmark run.")
    parser.add_argument("--workflow", required=True, help="Workflow group id, such as baseline, plan-first, or tdd")
    parser.add_argument("--task", required=True, help="Task id, matching benchmarks/tasks/{id}")
    parser.add_argument("--run-id", default=None, help="Run id. Defaults to UTC timestamp.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = prepare_run(ROOT, args.workflow, args.task, args.run_id)
    print(run_dir)
    print()
    print("Prepared target worktree:")
    print(f"- {run_dir / 'target'}")
    print()
    print("After the workflow modifies the target worktree, collect evidence with:")
    print("python scripts/execute_run.py \\")
    print(f"  --task benchmarks/tasks/{args.task}/task.json \\")
    print(f"  --run {run_dir / 'run.json'} \\")
    print("  --write")
    print()
    print("Then initialize manual scoring with:")
    print("python scripts/score_run.py \\")
    print(f"  --run {run_dir / 'run.json'} \\")
    print(f"  --score {run_dir / 'score.json'} \\")
    print("  --init \\")
    print("  --write")
    print()
    print("After filling score.json, calculate final score fields with:")
    print("python scripts/score_run.py \\")
    print(f"  --task benchmarks/tasks/{args.task}/task.json \\")
    print(f"  --run {run_dir / 'run.json'} \\")
    print(f"  --score {run_dir / 'score.json'} \\")
    print("  --write")
    print()
    print("Optional LLM review:")
    print("python scripts/llm_review_run.py \\")
    print(f"  --task benchmarks/tasks/{args.task}/task.json \\")
    print(f"  --run {run_dir / 'run.json'} \\")
    print("  --write")


if __name__ == "__main__":
    main()
