# Hook-Based Process Evidence

[Chinese version](hooks.zh-CN.md)

Hooks are an optional evidence layer for capturing what happened during coding. They do not score a run and they do not replace `execute_run.py`.

The shape is intentionally simple:

```text
Claude/Codex hook input -> record_hook_event.py -> events.jsonl -> summarize_run_events.py -> run.json
```

## Setup

Prepare a run first:

```bash
python scripts/prepare_run.py --workflow <workflow> --task <task-id>
```

Export the run environment printed by `prepare_run.py` before starting the coding agent:

```bash
export AI_EVAL_REPO=/path/to/ai-coding-evaluation
export AI_EVAL_RUN_DIR=/path/to/ai-coding-evaluation/runs/<workflow>/<task-id>/<run-id>
export AI_EVAL_TARGET_WORKTREE=$AI_EVAL_RUN_DIR/target
export AI_EVAL_PHASE=coding
```

Then start Claude Code or Codex from the prepared target worktree:

```bash
cd "$AI_EVAL_TARGET_WORKTREE"
```

Use `$AI_EVAL_RUN_DIR/task.md` as the coding prompt; use `$AI_EVAL_RUN_DIR/task.zh-CN.md` if you prefer Chinese. `acceptance.md` remains reviewer-only and is intentionally not copied into the run directory.

## Codex

Codex hooks require the feature flag:

```toml
[features]
codex_hooks = true
```

Use `integrations/codex/config.example.toml` and `integrations/codex/hooks.example.json` as copyable templates for `~/.codex/config.toml` and `~/.codex/hooks.json`, or for project-local `.codex/` config.

The template records:

```text
SessionStart
UserPromptSubmit
PreToolUse
PermissionRequest
PostToolUse
Stop
```

Codex hook coverage is useful but not a security boundary. Current Codex hooks do not intercept every possible shell or web path, so treat this as process evidence plus a light guardrail.

## Claude Code

Use `integrations/claude-code/settings.example.json` as a copyable template for Claude Code settings.

The template records:

```text
InstructionsLoaded
UserPromptSubmit
PreToolUse
PermissionRequest
PostToolUse
PostToolUseFailure
Stop
SessionEnd
```

Claude's `InstructionsLoaded` event makes `project_instructions_read` more reliable than best-effort file-read inference.

## What Gets Recorded

Hooks append normalized, redacted events to:

```text
runs/<workflow>/<task-id>/<run-id>/events.jsonl
```

Events keep summaries, not full content:

```text
source, session_id, turn_id, hook_event, model, cwd, tool_name
action.kind, action.command_summary, action.paths, action.success
classifications
```

The recorder redacts common API keys, tokens, passwords, bearer tokens, OpenAI-style `sk-*` keys, and JWT-like values. It does not store full prompts, file contents, or large tool output.

## Derived Fields

Run:

```bash
python scripts/summarize_run_events.py \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

`execute_run.py --write` also summarizes automatically when `events.jsonl` exists.

Derived fields include:

```text
model
models_used
human_interventions
permission_requests
process_evidence.project_instructions_read
process_evidence.relevant_docs_read
process_evidence.knowledge_sources_used
process_evidence.tools_used
process_evidence.self_review_performed
context_metrics.call_rate
context_metrics.hit_rate
event_collection
```

Unknown values stay unknown. The hook layer does not calculate `cost_usd`, hidden test results, adoption rate, or whether a plan was semantically followed.

## Guardrail

During `AI_EVAL_PHASE=coding`, the hook blocks tool calls that touch `acceptance.md`. `task.md` is the coding input; `acceptance.md` is review-only evidence.

This guardrail protects blind review discipline. It is not a sandbox.
