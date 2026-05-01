#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.score_run import REVIEW_DIMENSIONS, score_run


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_MAX_INPUT_CHARS = 60_000
DEFAULT_MAX_TOKENS = 2_000
REVIEW_SOURCE = "llm"
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"(?i)(authorization)\s*:\s*bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"sk-[A-Za-z0-9._\-]+"),
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def redact_secrets(text: str) -> str:
    redacted = text
    redacted = SECRET_PATTERNS[0].sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
    redacted = SECRET_PATTERNS[1].sub(lambda match: f"{match.group(1)}: Bearer <redacted>", redacted)
    redacted = SECRET_PATTERNS[2].sub("Bearer <redacted>", redacted)
    redacted = SECRET_PATTERNS[3].sub("sk-<redacted>", redacted)
    return redacted


def build_review_prompt(task_path: Path, run_path: Path, max_input_chars: int = DEFAULT_MAX_INPUT_CHARS) -> str:
    task_dir = task_path.parent
    run_dir = run_path.parent
    parts = [
        "# Task Contract",
        json.dumps(load_json(task_path), indent=2, sort_keys=True),
        "# Task Prompt",
        read_optional_text(task_dir / "task.md"),
        "# Acceptance Reference",
        read_optional_text(task_dir / "acceptance.md"),
        "# Run Facts",
        json.dumps(load_json(run_path), indent=2, sort_keys=True),
        "# Diff Patch",
        read_optional_text(run_dir / "diff.patch"),
        "# Test Log",
        read_optional_text(run_dir / "test.log"),
        "# Transcript",
        read_optional_text(run_dir / "transcript.md"),
    ]
    prompt = redact_secrets("\n\n".join(parts).strip())
    if len(prompt) > max_input_chars:
        raise ValueError(
            f"review input is too large: {len(prompt)} chars exceeds limit {max_input_chars}; "
            "trim evidence or pass a higher --max-input-chars value"
        )
    return prompt


def review_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["review", "review_notes"],
        "properties": {
            "review": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REVIEW_DIMENSIONS),
                "properties": {
                    dimension: {"type": "number", "minimum": 0, "maximum": 1}
                    for dimension in REVIEW_DIMENSIONS
                },
            },
            "review_notes": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REVIEW_DIMENSIONS),
                "properties": {dimension: {"type": "string"} for dimension in REVIEW_DIMENSIONS},
            },
        },
    }


def system_prompt() -> str:
    return """You are an AI coding evaluation reviewer.

Return JSON only. Review the final diff against the task prompt, acceptance reference, run facts, test log, and transcript.

Score each review dimension from 0.0 to 1.0:
- correctness: requested behavior is solved.
- regression_safety: existing behavior and public contracts remain safe.
- maintainability: implementation is simple, local, and readable.
- test_quality: tests and evidence are strong enough for the task.
- security: no new security risk or sensitive data exposure.
- process_compliance: coding process evidence shows expected project instructions, tools, planning, and self-review.

Output exactly:
{
  "review": {
    "correctness": 0.0,
    "regression_safety": 0.0,
    "maintainability": 0.0,
    "test_quality": 0.0,
    "security": 0.0,
    "process_compliance": 0.0
  },
  "review_notes": {
    "correctness": "short rationale",
    "regression_safety": "short rationale",
    "maintainability": "short rationale",
    "test_quality": "short rationale",
    "security": "short rationale",
    "process_compliance": "short rationale"
  }
}
"""


def response_format(mode: str) -> dict[str, Any]:
    if mode == "json_schema":
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "ai_coding_run_review",
                "strict": True,
                "schema": review_output_schema(),
            },
        }
    return {"type": "json_object"}


def chat_completions_endpoint(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def send_chat_completion(
    *,
    base_url: str,
    model: str,
    api_key: str,
    prompt: str,
    response_mode: str,
    max_tokens: int,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "response_format": response_format(response_mode),
    }
    request = urllib.request.Request(
        chat_completions_endpoint(base_url),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM review request failed: HTTP {error.code} {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"LLM review request failed: {error.reason}") from error

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("LLM response did not match OpenAI chat completions shape") from error


def parse_llm_json(content: str) -> dict[str, Any]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError("LLM response is not valid JSON") from error
    if not isinstance(data, dict):
        raise ValueError("LLM response JSON must be an object")
    return data


def validate_llm_review(data: dict[str, Any]) -> dict[str, Any]:
    review = data.get("review")
    if not isinstance(review, dict):
        raise ValueError("LLM response must include review object")
    normalized_review: dict[str, float] = {}
    for dimension in REVIEW_DIMENSIONS:
        value = review.get(dimension)
        if not isinstance(value, (int, float)):
            raise ValueError(f"review.{dimension} must be a number")
        if value < 0 or value > 1:
            raise ValueError(f"review.{dimension} must be between 0 and 1")
        normalized_review[dimension] = float(value)

    notes = data.get("review_notes", {})
    if not isinstance(notes, dict):
        raise ValueError("review_notes must be an object")
    normalized_notes = {str(key): str(value) for key, value in notes.items()}
    return {"review": normalized_review, "review_notes": normalized_notes}


def llm_review_run(
    task_path: Path,
    run_path: Path,
    score_path: Path | None = None,
    *,
    write: bool = False,
    base_url: str,
    model: str,
    api_key: str,
    response_mode: str = "json_object",
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict[str, Any]:
    task = load_json(task_path)
    run = load_json(run_path)
    output_path = score_path or run_path.parent / "score.json"
    existing = load_json(output_path) if output_path.exists() else {}
    prompt = build_review_prompt(task_path, run_path, max_input_chars=max_input_chars)
    content = send_chat_completion(
        base_url=base_url,
        model=model,
        api_key=api_key,
        prompt=prompt,
        response_mode=response_mode,
        max_tokens=max_tokens,
    )
    llm_review = validate_llm_review(parse_llm_json(content))
    score_doc = {
        "workflow_id": run.get("workflow_id", ""),
        "task_id": run.get("task_id", ""),
        "review": llm_review["review"],
        "review_sources": {dimension: REVIEW_SOURCE for dimension in REVIEW_DIMENSIONS},
        "review_notes": llm_review["review_notes"],
        "manual_hard_gates": existing.get("manual_hard_gates", []),
    }
    score_doc.update(score_run(task, run, score_doc))

    if write:
        write_json(output_path, score_doc)

    return score_doc


def env_or_default(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value else default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use an OpenAI-compatible LLM to review a run and write score.json.")
    parser.add_argument("--task", required=True, type=Path, help="Path to task.json")
    parser.add_argument("--run", required=True, type=Path, help="Path to run.json")
    parser.add_argument("--score-file", type=Path, default=None, help="Path to score.json")
    parser.add_argument("--write", action="store_true", help="Write score.json")
    parser.add_argument("--base-url", default=env_or_default("AI_EVAL_REVIEW_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=env_or_default("AI_EVAL_REVIEW_MODEL"))
    parser.add_argument("--api-key-env", default=env_or_default("AI_EVAL_REVIEW_API_KEY_ENV", DEFAULT_API_KEY_ENV))
    parser.add_argument("--response-mode", choices=["json_object", "json_schema"], default="json_object")
    parser.add_argument("--max-input-chars", type=int, default=int(env_or_default("AI_EVAL_REVIEW_MAX_INPUT_CHARS", str(DEFAULT_MAX_INPUT_CHARS))))
    parser.add_argument("--max-tokens", type=int, default=int(env_or_default("AI_EVAL_REVIEW_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.model:
        raise SystemExit("--model or AI_EVAL_REVIEW_MODEL is required")
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise SystemExit(f"missing API key env var: {args.api_key_env}")

    result = llm_review_run(
        args.task,
        args.run,
        args.score_file,
        write=args.write,
        base_url=args.base_url,
        model=args.model,
        api_key=api_key,
        response_mode=args.response_mode,
        max_input_chars=args.max_input_chars,
        max_tokens=args.max_tokens,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
