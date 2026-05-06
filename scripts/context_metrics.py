#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            events.append(json.loads(line))
    return events


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 3)


def event_context(event: dict[str, Any]) -> dict[str, str] | None:
    context = event.get("context")
    if isinstance(context, dict) and context.get("type") and context.get("id"):
        return {
            "type": str(context.get("type")),
            "id": str(context.get("id")),
            "classification_source": str(context.get("classification_source") or "unknown"),
        }

    classes = event.get("classifications", [])
    class_set = {str(value) for value in classes} if isinstance(classes, list) else set()
    action = event.get("action", {}) if isinstance(event.get("action"), dict) else {}
    paths = action.get("paths", []) if isinstance(action.get("paths"), list) else []
    summary = str(action.get("command_summary") or event.get("tool_name") or "unknown")
    tool_name = str(event.get("tool_name") or "")

    if "web_context" in class_set:
        return {"type": "web", "id": summary or tool_name or "web", "classification_source": "legacy"}
    if tool_name.startswith("mcp__"):
        return {"type": "mcp", "id": tool_name, "classification_source": "legacy"}
    if "read_docs" in class_set:
        context_id = str(paths[0]) if paths else summary
        return {"type": heuristic_context_type(context_id), "id": context_id, "classification_source": "legacy"}
    return None


def heuristic_context_type(path: str) -> str:
    normalized = path.replace("\\", "/").lower()
    basename = normalized.rstrip("/").split("/")[-1]
    if "/docs/contexts/" in normalized or normalized.startswith("docs/contexts/"):
        return "knowledge"
    if "/docs/components/" in normalized or normalized.startswith("docs/components/"):
        return "component_doc"
    if "/skills/" in normalized or "/.codex/skills/" in normalized or "/.claude/agents/" in normalized:
        return "skill"
    if normalized.startswith("specs/") or "/specs/" in normalized or basename in {"task.md", "task.zh-cn.md"}:
        return "spec"
    if basename in {"agents.md", "claude.md", "readme.md", "readme.zh-cn.md", "go.mod", "package.json"}:
        return "project_doc"
    if normalized.startswith("docs/") or "/docs/" in normalized:
        return "project_doc"
    return "unknown"


def result_summary(event: dict[str, Any]) -> dict[str, Any] | None:
    action = event.get("action", {})
    if not isinstance(action, dict):
        return None
    summary = action.get("result_summary")
    return summary if isinstance(summary, dict) else None


def event_success(event: dict[str, Any]) -> bool:
    action = event.get("action", {})
    if not isinstance(action, dict):
        return True
    return action.get("success") is not False


def context_hit(event: dict[str, Any]) -> bool:
    summary = result_summary(event)
    if summary is None:
        return event_success(event)
    return event_success(event) and summary.get("observed") is True and summary.get("empty") is False


def hit_mode(events: list[dict[str, Any]]) -> str:
    if not events:
        return "not_available"
    observed = [result_summary(event) is not None and result_summary(event).get("observed") is True for event in events]
    if all(observed):
        return "true_hit"
    if not any(observed):
        return "legacy_proxy"
    return "mixed"


def adoption_rate_for_runs(runs: list[dict[str, Any]]) -> float | None:
    generated = 0
    accepted = 0
    has_line_counts = False
    run_rates: list[float] = []
    for run in runs:
        adoption = run.get("adoption", {})
        if not isinstance(adoption, dict):
            continue
        ai_lines = adoption.get("ai_generated_lines")
        accepted_lines = adoption.get("accepted_lines")
        if is_number(ai_lines) and is_number(accepted_lines):
            generated += int(ai_lines)
            accepted += int(accepted_lines)
            has_line_counts = True
        elif is_number(adoption.get("adoption_rate")):
            run_rates.append(float(adoption["adoption_rate"]))

    if has_line_counts:
        return round(accepted / generated, 3) if generated else None
    if run_rates:
        return round(mean(run_rates), 3)
    return None


def summarize_group(
    *,
    total_observed_runs: int,
    run_records: list[dict[str, Any]],
    context_events_by_run: dict[Path, list[dict[str, Any]]],
) -> dict[str, Any]:
    runs_with_call = [run for run in run_records if context_events_by_run.get(Path(run["_run_dir"]))]
    runs_with_hit = [
        run
        for run in runs_with_call
        if any(context_hit(event) for event in context_events_by_run.get(Path(run["_run_dir"]), []))
    ]
    events = [event for events in context_events_by_run.values() for event in events]
    return {
        "observed_runs": total_observed_runs,
        "runs_with_context_call": len(runs_with_call),
        "runs_with_context_hit": len(runs_with_hit),
        "call_rate": rate(len(runs_with_call), total_observed_runs),
        "hit_rate": rate(len(runs_with_hit), len(runs_with_call)),
        "adoption_rate": adoption_rate_for_runs(runs_with_call),
        "hit_mode": hit_mode(events),
    }


def collect_context_metrics_from_run_paths(run_paths: list[Path]) -> dict[str, Any]:
    observed_runs: list[dict[str, Any]] = []
    all_context_events_by_run: dict[Path, list[dict[str, Any]]] = {}
    type_events_by_run: dict[str, dict[Path, list[dict[str, Any]]]] = {}
    item_events_by_run: dict[tuple[str, str], dict[Path, list[dict[str, Any]]]] = {}

    for run_path in sorted(run_paths):
        run_dir = run_path.parent
        events = load_events(run_dir / "events.jsonl")
        if not events:
            continue
        run = load_json(run_path)
        run["_run_dir"] = str(run_dir)
        observed_runs.append(run)

        for event in events:
            context = event_context(event)
            if not context:
                continue
            all_context_events_by_run.setdefault(run_dir, []).append(event)
            context_type = context["type"]
            context_id = context["id"]
            type_events_by_run.setdefault(context_type, {}).setdefault(run_dir, []).append(event)
            item_events_by_run.setdefault((context_type, context_id), {}).setdefault(run_dir, []).append(event)

    observed_count = len(observed_runs)
    overall = summarize_group(
        total_observed_runs=observed_count,
        run_records=observed_runs,
        context_events_by_run=all_context_events_by_run,
    )

    by_type = []
    for context_type, events_by_run in sorted(type_events_by_run.items()):
        summary = summarize_group(
            total_observed_runs=observed_count,
            run_records=observed_runs,
            context_events_by_run=events_by_run,
        )
        summary["context_type"] = context_type
        by_type.append(summary)

    by_item = []
    for (context_type, context_id), events_by_run in sorted(item_events_by_run.items()):
        summary = summarize_group(
            total_observed_runs=observed_count,
            run_records=observed_runs,
            context_events_by_run=events_by_run,
        )
        summary["context_type"] = context_type
        summary["context_id"] = context_id
        by_item.append(summary)

    return {
        **overall,
        "generated_at": utc_now(),
        "by_type": by_type,
        "by_item": by_item,
    }


def collect_context_metrics(runs_root: Path) -> dict[str, Any]:
    return collect_context_metrics_from_run_paths(list(runs_root.glob("*/*/*/run.json")))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate cross-run context link metrics from hook events.")
    parser.add_argument("--runs", type=Path, default=Path("runs"), help="Runs root directory")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = collect_context_metrics(args.runs)
    if args.output:
        write_json(args.output, metrics)
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
