from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


UNKNOWN = "unknown"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_scored(run: dict[str, Any]) -> bool:
    return is_number(run.get("score"))


def first_pass(run: dict[str, Any]) -> bool:
    return run.get("tests", {}).get("required_passed") is True and not run.get("hard_gates")


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return mean(values)


def numeric_values(runs: list[dict[str, Any]], key: str) -> list[float]:
    return [float(run[key]) for run in runs if is_number(run.get(key))]


def model_label(run: dict[str, Any]) -> str:
    model = run.get("model")
    if isinstance(model, str) and model:
        return model
    models = run.get("models_used")
    if isinstance(models, list) and models:
        first = models[0]
        if isinstance(first, str) and first:
            return first
    return UNKNOWN


def task_metadata(task: dict[str, Any] | None) -> dict[str, str]:
    if not task:
        return {
            "task_type": UNKNOWN,
            "effort_size": UNKNOWN,
            "business_complexity": UNKNOWN,
            "context_maturity": UNKNOWN,
        }
    complexity = task.get("complexity", {})
    return {
        "task_type": str(task.get("type") or UNKNOWN),
        "effort_size": str(task.get("effort_size") or UNKNOWN),
        "business_complexity": str(complexity.get("business_complexity") or UNKNOWN),
        "context_maturity": str(complexity.get("context_maturity") or UNKNOWN),
    }


def collect_tasks(root: Path | None) -> dict[str, dict[str, Any]]:
    if root is None or not root.exists():
        return {}
    tasks: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*/task.json")):
        task = load_json(path)
        task_id = str(task.get("id") or path.parent.name)
        tasks[task_id] = task
    return tasks


def collect_runs(root: Path, tasks_root: Path | None = None) -> list[dict[str, Any]]:
    tasks = collect_tasks(tasks_root)
    runs: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/*/*/run.json")):
        if path.parent.name == "latest":
            continue

        data = load_json(path)
        score_path = path.parent / "score.json"
        if score_path.exists():
            data.update(load_json(score_path))

        task_id = str(data.get("task_id") or path.parent.parent.name)
        data.update(task_metadata(tasks.get(task_id)))
        data["task_id"] = task_id
        data["run_id"] = path.parent.name
        data["model_label"] = model_label(data)
        data["scored"] = is_scored(data)
        data["_run_path"] = str(path)
        data["_score_path"] = str(score_path)
        data["_path"] = str(score_path if score_path.exists() else path)
        runs.append(data)
    return runs


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [run for run in runs if is_scored(run)]
    first_passes = [run for run in scored if first_pass(run)]
    gated = [run for run in scored if run.get("hard_gates")]
    return {
        "runs": len(runs),
        "scored_runs": len(scored),
        "avg_score": mean_or_none(numeric_values(scored, "score")),
        "avg_raw_score": mean_or_none(numeric_values(scored, "raw_score")),
        "avg_attention_score": mean_or_none(numeric_values(scored, "attention_adjusted_score")),
        "avg_duration_minutes": mean_or_none(numeric_values(scored, "duration_minutes")),
        "avg_human_interventions": mean_or_none(numeric_values(scored, "human_interventions")),
        "first_pass_rate": len(first_passes) / len(scored) if scored else None,
        "gate_rate": len(gated) / len(scored) if scored else None,
    }


def group_by(runs: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        value = run.get(key)
        label = str(value) if value not in (None, "") else UNKNOWN
        groups.setdefault(label, []).append(run)
    return groups
