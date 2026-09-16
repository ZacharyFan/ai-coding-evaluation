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


DEFAULT_REFERENCE_WORKFLOW = "baseline"


def arm_key(run: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(run.get("workflow_id") or UNKNOWN),
        str(run.get("task_id") or UNKNOWN),
        str(run.get("model_label") or UNKNOWN),
    )


def arm_records(runs: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Aggregate scored runs into arms keyed by (workflow, task, model)."""
    scores_by_arm: dict[tuple[str, str, str], list[float]] = {}
    for run in runs:
        if not is_scored(run):
            continue
        scores_by_arm.setdefault(arm_key(run), []).append(float(run["score"]))
    return {
        key: {"scores": scores, "mean_score": mean(scores)} for key, scores in scores_by_arm.items()
    }


def paired_deltas(
    runs: list[dict[str, Any]], reference_workflow: str = DEFAULT_REFERENCE_WORKFLOW
) -> list[dict[str, Any]]:
    """Pair candidate arms with the reference workflow on (task, model) and diff the means.

    Task difficulty cancels inside a pair, so deltas isolate the workflow difference.
    A candidate arm whose (task, model) key has no reference arm yields no pair.
    """
    arms = arm_records(runs)
    reference_means = {
        (task_id, model_label): arm["mean_score"]
        for (workflow_id, task_id, model_label), arm in arms.items()
        if workflow_id == reference_workflow
    }
    deltas: list[dict[str, Any]] = []
    for (workflow_id, task_id, model_label), arm in sorted(arms.items()):
        if workflow_id == reference_workflow:
            continue
        reference_mean = reference_means.get((task_id, model_label))
        if reference_mean is None:
            continue
        deltas.append(
            {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "model_label": model_label,
                "candidate_mean": round(arm["mean_score"], 2),
                "reference_mean": round(reference_mean, 2),
                "delta": round(arm["mean_score"] - reference_mean, 2),
            }
        )
    return deltas


def paired_summary(
    runs: list[dict[str, Any]], reference_workflow: str = DEFAULT_REFERENCE_WORKFLOW
) -> dict[str, Any]:
    """Summarize paired deltas per candidate workflow.

    coverage = pairs / candidate arms; sign_consistency = max(positive, negative) / pairs.
    """
    arms = arm_records(runs)
    deltas = paired_deltas(runs, reference_workflow)

    arms_by_workflow: dict[str, int] = {}
    for workflow_id, _task_id, _model_label in sorted(arms):
        if workflow_id != reference_workflow:
            arms_by_workflow[workflow_id] = arms_by_workflow.get(workflow_id, 0) + 1

    deltas_by_workflow: dict[str, list[dict[str, Any]]] = {}
    for delta in deltas:
        deltas_by_workflow.setdefault(delta["workflow_id"], []).append(delta)

    by_workflow: dict[str, dict[str, Any]] = {}
    for workflow_id, arm_count in arms_by_workflow.items():
        workflow_deltas = deltas_by_workflow.get(workflow_id, [])
        pairs = len(workflow_deltas)
        positive = sum(1 for delta in workflow_deltas if delta["delta"] > 0)
        negative = sum(1 for delta in workflow_deltas if delta["delta"] < 0)
        by_workflow[workflow_id] = {
            "arms": arm_count,
            "pairs": pairs,
            "coverage": pairs / arm_count if arm_count else None,
            "mean_delta": mean([delta["delta"] for delta in workflow_deltas]) if pairs else None,
            "positive": positive,
            "negative": negative,
            "sign_consistency": max(positive, negative) / pairs if pairs else None,
        }
    return {
        "reference_workflow": reference_workflow,
        "pairs_total": len(deltas),
        "by_workflow": by_workflow,
    }
