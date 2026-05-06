#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"(?i)(authorization)\s*:\s*bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"sk-[A-Za-z0-9._\-]+"),
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),
)

DOC_FILENAMES = {
    "agents.md",
    "claude.md",
    "readme.md",
    "readme.zh-cn.md",
    "task.md",
    "pyproject.toml",
    "package.json",
    "go.mod",
    "cargo.toml",
    "requirements.txt",
}

EDIT_TOOLS = {"edit", "write", "multiedit", "apply_patch"}
READ_TOOLS = {"read", "grep", "glob", "ls"}
SHELL_TOOLS = {"bash", "shell"}
WEB_TOOLS = {"webfetch", "websearch", "web_search"}
CONTEXT_SOURCE_TYPES = {"spec", "project_doc", "knowledge", "component_doc", "skill", "web", "mcp", "unknown"}
TEST_COMMAND_PATTERN = re.compile(
    r"(^|\s)(go test|pytest|python -m pytest|npm test|pnpm test|yarn test|cargo test|mvn test|gradle test|"
    r"jest|vitest|unittest|lint|typecheck|build|(?:\./)?scripts/run_eval_case\.sh)(\s|$)"
)
DIFF_COMMAND_PATTERN = re.compile(r"(^|\s)git\s+(diff|status|show)(\s|$)")
PATH_KEY_PATTERN = re.compile(r"(^|_)(file|path|cwd|directory)(_|$)", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact_secrets(text: str) -> str:
    redacted = text
    redacted = SECRET_PATTERNS[0].sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
    redacted = SECRET_PATTERNS[1].sub(lambda match: f"{match.group(1)}: Bearer <redacted>", redacted)
    redacted = SECRET_PATTERNS[2].sub("Bearer <redacted>", redacted)
    redacted = SECRET_PATTERNS[3].sub("sk-<redacted>", redacted)
    redacted = SECRET_PATTERNS[4].sub("<redacted-jwt>", redacted)
    return redacted


def short_text(value: Any, limit: int = 240) -> str:
    text = redact_secrets(str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def tool_key(tool_name: str | None) -> str:
    return (tool_name or "").strip().lower()


def looks_like_path(value: str) -> bool:
    if not value or value.startswith("-"):
        return False
    lowered = value.lower()
    return (
        "/" in value
        or lowered.endswith((".md", ".json", ".toml", ".yaml", ".yml", ".go", ".py", ".ts", ".tsx", ".js", ".jsx"))
        or lowered in DOC_FILENAMES
    )


def extract_command_paths(command: str) -> list[str]:
    if "*** Begin Patch" in command:
        patch_paths = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", command, flags=re.MULTILINE)
        patch_paths.extend(re.findall(r"^\*\*\* Move to: (.+)$", command, flags=re.MULTILINE))
        return unique([redact_secrets(path.strip()) for path in patch_paths if path.strip()])

    paths: list[str] = []
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    for part in parts:
        cleaned = part.strip("\"'`:,;")
        if looks_like_path(cleaned):
            paths.append(redact_secrets(cleaned))
    return unique(paths)


def extract_paths(value: Any, parent_key: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"content", "prompt", "stdout", "stderr", "output"}:
                continue
            paths.extend(extract_paths(child, key))
    elif isinstance(value, list):
        for item in value:
            paths.extend(extract_paths(item, parent_key))
    elif isinstance(value, str):
        if parent_key == "command":
            paths.extend(extract_command_paths(value))
        elif PATH_KEY_PATTERN.search(parent_key) or looks_like_path(value):
            cleaned = value.strip()
            if looks_like_path(cleaned):
                paths.append(redact_secrets(cleaned))
    return unique(paths)


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
    return path.replace("\\", "/").strip()


def is_acceptance_path(path: str) -> bool:
    return path_basename(path) == "acceptance.md"


def is_doc_path(path: str) -> bool:
    normalized = normalized_path(path).lower()
    return (
        path_basename(path) in DOC_FILENAMES
        or normalized.startswith("docs/")
        or "/docs/" in normalized
        or normalized.endswith("/docs")
    )


def is_context_class(classes: list[str]) -> bool:
    return any(value in {"read_docs", "web_context"} for value in classes)


def output_text_from_response(tool_response: Any) -> str | None:
    if isinstance(tool_response, str):
        return redact_secrets(tool_response)
    if not isinstance(tool_response, dict):
        return None
    for key in ("stdout", "output", "content", "text", "body"):
        value = tool_response.get(key)
        if isinstance(value, str):
            return redact_secrets(value)
    return None


def list_result_from_response(tool_response: Any) -> list[Any] | None:
    if isinstance(tool_response, list):
        return tool_response
    if not isinstance(tool_response, dict):
        return None
    for key in ("results", "items", "data", "matches"):
        value = tool_response.get(key)
        if isinstance(value, list):
            return value
    return None


def result_summary(tool_response: Any, command_summary_value: str) -> dict[str, Any]:
    text = output_text_from_response(tool_response)
    if text is not None:
        stripped = text.strip()
        lines = [line for line in stripped.splitlines() if line.strip()]
        is_search = bool(re.search(r"(^|\s)(rg|grep|find|search)(\s|$)", command_summary_value.lower()))
        return {
            "observed": True,
            "empty": not bool(stripped),
            "result_count": len(lines) if is_search else None,
            "output_chars": len(text),
            "line_count": len(lines),
            "summary": "empty_text" if not stripped else "non_empty_text",
        }

    result_list = list_result_from_response(tool_response)
    if result_list is not None:
        return {
            "observed": True,
            "empty": len(result_list) == 0,
            "result_count": len(result_list),
            "output_chars": None,
            "line_count": None,
            "summary": "empty_list" if not result_list else "json_list",
        }

    if isinstance(tool_response, dict):
        meaningful_keys = [key for key in tool_response if key not in {"success", "ok", "exit_code", "exitCode", "returncode"}]
        if meaningful_keys:
            return {
                "observed": True,
                "empty": False,
                "result_count": None,
                "output_chars": None,
                "line_count": None,
                "summary": "json_object",
            }

    return {
        "observed": False,
        "empty": True,
        "result_count": None,
        "output_chars": None,
        "line_count": None,
        "summary": "not_observed",
    }


def path_matches_glob(path: str, pattern: str) -> bool:
    normalized = normalized_path(path).lstrip("./")
    normalized_pattern = normalized_path(pattern).lstrip("./")
    if fnmatch.fnmatch(normalized, normalized_pattern):
        return True
    return normalized.endswith("/" + normalized_pattern.rstrip("*")) or fnmatch.fnmatch(normalized.split("/target/", 1)[-1], normalized_pattern)


def configured_context(
    paths: list[str],
    tool_name: str | None,
    context_sources: list[dict[str, Any]] | None,
) -> dict[str, str] | None:
    if not context_sources:
        return None
    tool = tool_name or ""
    for source in context_sources:
        source_type = str(source.get("type") or "")
        if source_type not in CONTEXT_SOURCE_TYPES - {"unknown"}:
            continue
        for pattern in source.get("path_globs") or []:
            if not isinstance(pattern, str):
                continue
            for path in paths:
                if path_matches_glob(path, pattern):
                    return {"type": source_type, "id": normalized_path(path), "classification_source": "configured"}
        for configured_tool in source.get("tool_names") or []:
            if isinstance(configured_tool, str) and configured_tool == tool:
                return {"type": source_type, "id": tool, "classification_source": "configured"}
    return None


def heuristic_context_type(path: str) -> str | None:
    normalized = normalized_path(path).lower()
    basename = path_basename(path)
    if "/docs/contexts/" in normalized or normalized.startswith("docs/contexts/"):
        return "knowledge"
    if "/docs/components/" in normalized or normalized.startswith("docs/components/"):
        return "component_doc"
    if "/skills/" in normalized or "/.codex/skills/" in normalized or "/.claude/agents/" in normalized:
        return "skill"
    if normalized.startswith("specs/") or "/specs/" in normalized or basename in {"task.md", "task.zh-cn.md"}:
        return "spec"
    if is_doc_path(path):
        return "project_doc"
    return None


def context_metadata(
    tool_name: str | None,
    summary: str,
    paths: list[str],
    classes: list[str],
    context_sources: list[dict[str, Any]] | None,
) -> dict[str, str] | None:
    configured = configured_context(paths, tool_name, context_sources)
    if configured:
        return configured

    key = tool_key(tool_name)
    if "web_context" in classes:
        return {"type": "web", "id": short_text(summary or tool_name or "web"), "classification_source": "adapter"}
    if key.startswith("mcp__"):
        return {"type": "mcp", "id": tool_name or "mcp", "classification_source": "adapter"}

    for path in paths:
        context_type = heuristic_context_type(path)
        if context_type:
            return {"type": context_type, "id": normalized_path(path), "classification_source": "heuristic"}

    if is_context_class(classes):
        return {"type": "unknown", "id": short_text(summary or tool_name or "unknown"), "classification_source": "unknown"}
    return None


def command_from_input(tool_input: Any) -> str:
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "cmd"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return short_text(value)
    return ""


def tool_success(hook_event: str, tool_response: Any) -> bool | None:
    if hook_event == "PostToolUseFailure":
        return False
    if hook_event != "PostToolUse":
        return None
    if isinstance(tool_response, dict):
        for key in ("success", "ok"):
            if isinstance(tool_response.get(key), bool):
                return bool(tool_response[key])
        for key in ("exit_code", "exitCode", "returncode"):
            if isinstance(tool_response.get(key), int):
                return int(tool_response[key]) == 0
    return True


def action_kind(tool_name: str | None, hook_event: str) -> str:
    key = tool_key(tool_name)
    if key in SHELL_TOOLS:
        return "shell"
    if key in EDIT_TOOLS or key.startswith("mcp__") and any(part in key for part in ("write", "edit", "create")):
        return "edit"
    if key in READ_TOOLS or key.startswith("mcp__") and any(part in key for part in ("read", "search", "list", "get")):
        return "read"
    if key in WEB_TOOLS or "web" in key:
        return "web"
    if hook_event in {"UserPromptSubmit", "Stop", "SessionStart", "SessionEnd", "InstructionsLoaded"}:
        return "lifecycle"
    if hook_event == "PermissionRequest":
        return "permission"
    return "tool"


def command_summary(tool_name: str | None, hook_event: str, tool_input: Any, raw: dict[str, Any]) -> str:
    key = tool_key(tool_name)
    if key == "apply_patch":
        return "apply_patch"
    if key in EDIT_TOOLS:
        return short_text(tool_name or "edit")
    if key in SHELL_TOOLS:
        command = command_from_input(tool_input)
        if command:
            return command
    if hook_event == "UserPromptSubmit":
        prompt = raw.get("prompt", "")
        return f"user_prompt_chars={len(prompt) if isinstance(prompt, str) else 0}"
    if hook_event == "Stop":
        message = raw.get("last_assistant_message", "")
        return f"assistant_message_chars={len(message) if isinstance(message, str) else 0}"
    if hook_event == "InstructionsLoaded":
        return "instructions_loaded"
    if hook_event == "SessionStart":
        return f"session_start:{raw.get('source', '')}".rstrip(":")
    if hook_event == "SessionEnd":
        return f"session_end:{raw.get('reason', '')}".rstrip(":")
    return short_text(tool_name or hook_event)


def classify(tool_name: str | None, hook_event: str, summary: str, paths: list[str]) -> list[str]:
    classes: list[str] = []
    key = tool_key(tool_name)
    if hook_event in {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest"} and tool_name:
        classes.append("tool_use")
    if hook_event == "UserPromptSubmit":
        classes.append("user_prompt")
    if hook_event == "PermissionRequest":
        classes.append("permission_request")
    if hook_event == "InstructionsLoaded":
        classes.append("read_docs")
    if key in EDIT_TOOLS or key.startswith("mcp__") and any(part in key for part in ("write", "edit", "create")):
        classes.append("code_edit")
    if key in WEB_TOOLS or "web" in key:
        classes.append("web_context")
    if any(is_acceptance_path(path) for path in paths) or "acceptance.md" in summary.lower():
        classes.append("read_acceptance")
    if any(is_doc_path(path) for path in paths):
        classes.append("read_docs")
    lowered_summary = summary.lower()
    if TEST_COMMAND_PATTERN.search(lowered_summary):
        classes.append("test_run")
    if DIFF_COMMAND_PATTERN.search(lowered_summary):
        classes.append("diff_review")
    return unique(classes)


def normalize_hook_event(
    raw: dict[str, Any],
    adapter: str,
    *,
    blocked: bool = False,
    context_sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    hook_event = str(raw.get("hook_event_name") or raw.get("hookEventName") or "")
    tool_name = raw.get("tool_name")
    tool_input = raw.get("tool_input", {})
    paths = extract_paths(tool_input)
    summary = command_summary(tool_name, hook_event, tool_input, raw)
    classifications = classify(tool_name, hook_event, summary, paths)
    success = tool_success(hook_event, raw.get("tool_response"))
    action = {
        "kind": action_kind(tool_name, hook_event),
        "command_summary": summary,
        "paths": paths,
        "success": success,
        "result_summary": result_summary(raw.get("tool_response"), summary),
    }
    if blocked:
        action["blocked"] = True

    event = {
        "schema_version": "1",
        "timestamp": utc_now(),
        "source": adapter,
        "session_id": str(raw.get("session_id") or ""),
        "turn_id": str(raw.get("turn_id") or ""),
        "hook_event": hook_event,
        "model": raw.get("model"),
        "cwd": str(raw.get("cwd") or ""),
        "tool_name": tool_name,
        "action": action,
        "classifications": classifications,
    }
    context = context_metadata(tool_name, summary, paths, classifications, context_sources)
    if context:
        event["context"] = context
    return event


def load_context_sources(run_dir: Path) -> list[dict[str, Any]]:
    repo_root = Path(os.environ.get("AI_EVAL_REPO", "")).expanduser()
    run_path = run_dir / "run.json"
    if not repo_root or not run_path.exists():
        return []
    try:
        run = json.loads(run_path.read_text(encoding="utf-8"))
        task_id = run.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            return []
        task_path = repo_root / "benchmarks" / "tasks" / task_id / "task.json"
        if not task_path.exists():
            return []
        task = json.loads(task_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    sources = task.get("context_sources")
    return sources if isinstance(sources, list) else []


def should_block_acceptance(event: dict[str, Any]) -> bool:
    if os.environ.get("AI_EVAL_PHASE") != "coding":
        return False
    if event.get("hook_event") != "PreToolUse":
        return False
    action = event.get("action", {})
    paths = action.get("paths", [])
    summary = str(action.get("command_summary", "")).lower()
    return any(is_acceptance_path(str(path)) for path in paths) or "acceptance.md" in summary


def append_event(run_dir: Path, event: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(event, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(run_dir / "events.jsonl", os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def continue_output(hook_event: str) -> str:
    if hook_event in {"SessionStart", "UserPromptSubmit", "Stop"}:
        return json.dumps({"continue": True, "suppressOutput": True})
    return ""


def deny_output(adapter: str, reason: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def handle_hook_event(raw: dict[str, Any], adapter: str) -> str:
    run_dir_value = os.environ.get("AI_EVAL_RUN_DIR")
    run_dir = Path(run_dir_value).expanduser() if run_dir_value else None
    context_sources = load_context_sources(run_dir) if run_dir else []
    event = normalize_hook_event(raw, adapter, context_sources=context_sources)
    blocked = should_block_acceptance(event)
    if blocked:
        event = normalize_hook_event(raw, adapter, blocked=True, context_sources=context_sources)

    if run_dir:
        append_event(run_dir, event)

    if blocked:
        return deny_output(adapter, "acceptance.md is review-only evidence and cannot be read during coding.")
    return continue_output(event.get("hook_event", ""))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record Claude Code or Codex hook events as normalized JSONL.")
    parser.add_argument("--adapter", required=True, choices=["claude", "codex"], help="Hook input adapter")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        raw = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    output = handle_hook_event(raw, args.adapter)
    if output:
        print(output)


if __name__ == "__main__":
    main()
