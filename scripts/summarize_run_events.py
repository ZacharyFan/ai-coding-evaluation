#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTEXT_CLASSES = {"read_docs", "web_context"}
INSTRUCTION_FILENAMES = {"agents.md", "claude.md", "readme.md", "readme.zh-cn.md"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
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


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def path_basename(path: str) -> str:
    return path.replace("\\", "/").rstrip("/").split("/")[-1].lower()


def normalized_path(path: str) -> str:
    return path.replace("\\", "/")


def action(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("action", {})
    return value if isinstance(value, dict) else {}


def classifications(event: dict[str, Any]) -> set[str]:
    values = event.get("classifications", [])
    if not isinstance(values, list):
        return set()
    return {str(value) for value in values}


def event_success(event: dict[str, Any]) -> bool:
    success = action(event).get("success")
    return success is not False


def tool_summary(event: dict[str, Any]) -> str:
    summary = str(action(event).get("command_summary") or "").strip()
    if summary:
        return summary
    return str(event.get("tool_name") or "").strip()


def event_paths(event: dict[str, Any]) -> list[str]:
    paths = action(event).get("paths", [])
    if not isinstance(paths, list):
        return []
    return [normalized_path(str(path)) for path in paths if path]


def is_instruction_path(path: str) -> bool:
    normalized = normalized_path(path).lower()
    return path_basename(path) in INSTRUCTION_FILENAMES or "/.claude/rules/" in normalized


def project_instructions_read(events: list[dict[str, Any]]) -> bool:
    for event in events:
        if event.get("hook_event") == "InstructionsLoaded":
            return True
        if "read_docs" in classifications(event) and any(is_instruction_path(path) for path in event_paths(event)):
            return True
    return False


def relevant_docs_read(events: list[dict[str, Any]]) -> list[str]:
    docs: list[str] = []
    for event in events:
        if "read_docs" not in classifications(event):
            continue
        for path in event_paths(event):
            if path_basename(path) == "acceptance.md":
                continue
            docs.append(path)
    return unique(docs)


def knowledge_sources_used(events: list[dict[str, Any]]) -> list[str]:
    sources: list[str] = []
    for event in events:
        classes = classifications(event)
        tool_name = str(event.get("tool_name") or "")
        if "web_context" in classes:
            sources.append(tool_summary(event) or tool_name)
        elif tool_name.startswith("mcp__") and "read_docs" not in classes:
            sources.append(tool_name)
    return unique(sources)


def tools_used(events: list[dict[str, Any]]) -> list[str]:
    tools: list[str] = []
    for event in events:
        if "tool_use" not in classifications(event):
            continue
        summary = tool_summary(event)
        if summary:
            tools.append(summary)
    return unique(tools)


def self_review_performed(events: list[dict[str, Any]]) -> bool:
    last_edit_index = -1
    for index, event in enumerate(events):
        if "code_edit" in classifications(event):
            last_edit_index = index
    if last_edit_index < 0:
        return False
    for event in events[last_edit_index + 1 :]:
        classes = classifications(event)
        if "test_run" in classes or "diff_review" in classes:
            return True
    return False


def model_fields(events: list[dict[str, Any]]) -> tuple[str | None, list[str]]:
    models = unique([str(event.get("model")) for event in events if event.get("model")])
    if not models:
        return None, []
    return models[0], models


def context_metrics(events: list[dict[str, Any]]) -> dict[str, float | None]:
    tool_events = [event for event in events if "tool_use" in classifications(event)]
    context_events = [event for event in tool_events if classifications(event) & CONTEXT_CLASSES]
    if not tool_events:
        call_rate = None
    else:
        call_rate = round(len(context_events) / len(tool_events), 3)

    if not context_events:
        hit_rate = None
    else:
        successful = [event for event in context_events if event_success(event)]
        hit_rate = round(len(successful) / len(context_events), 3)

    return {"call_rate": call_rate, "hit_rate": hit_rate}


def human_interventions(events: list[dict[str, Any]]) -> int | None:
    prompt_count = sum(1 for event in events if "user_prompt" in classifications(event))
    if prompt_count == 0:
        return None
    return max(0, prompt_count - 1)


def permission_requests(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events if "permission_request" in classifications(event))


def ensure_optional_objects(run: dict[str, Any]) -> None:
    adoption = dict(run.get("adoption", {}))
    adoption.setdefault("ai_generated_lines", None)
    adoption.setdefault("accepted_lines", None)
    adoption.setdefault("adoption_rate", None)
    run["adoption"] = adoption

    metrics = dict(run.get("context_metrics", {}))
    metrics.setdefault("call_rate", None)
    metrics.setdefault("hit_rate", None)
    metrics.setdefault("adoption_rate", None)
    run["context_metrics"] = metrics


def summarize_run_events(run_path: Path, *, write: bool = False) -> dict[str, Any]:
    run = load_json(run_path)
    events_path = run_path.parent / "events.jsonl"
    events = load_events(events_path)
    if not events:
        return run

    ensure_optional_objects(run)
    model, models = model_fields(events)
    if model:
        run["model"] = model
        run["models_used"] = models

    interventions = human_interventions(events)
    if interventions is not None:
        run["human_interventions"] = interventions

    run["permission_requests"] = permission_requests(events)

    process = dict(run.get("process_evidence", {}))
    process["project_instructions_read"] = project_instructions_read(events)
    process["relevant_docs_read"] = unique(process.get("relevant_docs_read", []) + relevant_docs_read(events))
    process["knowledge_sources_used"] = unique(
        process.get("knowledge_sources_used", []) + knowledge_sources_used(events)
    )
    process["tools_used"] = unique(process.get("tools_used", []) + tools_used(events))
    process.setdefault("plan_followed", False)
    process["self_review_performed"] = self_review_performed(events)
    run["process_evidence"] = process

    metrics = dict(run.get("context_metrics", {}))
    derived_metrics = context_metrics(events)
    metrics["call_rate"] = derived_metrics["call_rate"]
    metrics["hit_rate"] = derived_metrics["hit_rate"]
    metrics.setdefault("adoption_rate", None)
    run["context_metrics"] = metrics

    run["event_collection"] = {
        "events_path": str(events_path),
        "event_count": len(events),
        "sources": unique([str(event.get("source")) for event in events if event.get("source")]),
        "summarized_at": utc_now(),
    }

    if write:
        write_json(run_path, run)
    return run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize hook events into run.json process evidence.")
    parser.add_argument("--run", required=True, type=Path, help="Path to run.json")
    parser.add_argument("--write", action="store_true", help="Write derived fields back to run.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = summarize_run_events(args.run, write=args.write)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
