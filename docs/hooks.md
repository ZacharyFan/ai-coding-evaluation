# Hook-Based Process Evidence

[Chinese version](hooks.zh-CN.md)

Hooks are an optional evidence layer for capturing what happened during coding. They do not score a run and they do not replace `python -m scripts.collect_run`.

The shape is intentionally simple:

```text
Claude/Codex hook input -> record_hook_event.py -> events.jsonl -> summarize_run_events.py -> run.json
```

## Setup

Prepare a run first:

```bash
python -m scripts.eval start --workflow <workflow> --task <task-id> [--model <model>]
```

Export the run environment before starting the coding agent:

```bash
eval "$(python -m scripts.eval env)"
```

If you are outside the evaluation repo root, use the thin helper:

```bash
eval "$(/absolute/path/to/ai-coding-evaluation/bin/ai-eval env)"
```

`scripts.eval env` prints absolute paths, so the exported environment keeps working after you `cd` into the target worktree.

Then start Claude Code or Codex from the same shell:

```bash
cd "$AI_EVAL_TARGET_WORKTREE"
```

The agent must be launched after `eval` so the hook process inherits `AI_EVAL_REPO`, `AI_EVAL_RUN_DIR`, `AI_EVAL_TARGET_WORKTREE`, and `AI_EVAL_PHASE`. Environment changes do not retroactively affect already-running Codex or Claude sessions.

Use the task file copied into the run directory as the coding prompt: `runs/<workflow>/<task-id>/<run-id>/task.md`, or `task.zh-CN.md` if you prefer Chinese. `acceptance.md` remains reviewer-only and is intentionally not copied into the run directory.

## Codex

Codex hooks require the feature flag:

```toml
[features]
codex_hooks = true
```

Use `integrations/codex/config.example.toml` and `integrations/codex/hooks.example.json` as copyable templates for Codex configuration. The hook command intentionally uses `$AI_EVAL_REPO`, so run `eval "$(python -m scripts.eval env)"` before launching Codex, or use `bin/ai-eval env` when outside the repo root.

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

Use `integrations/claude-code/settings.example.json` as a copyable template for Claude Code settings. Claude Code settings can live in:

```text
~/.claude/settings.json
.claude/settings.json
.claude/settings.local.json
```

Copy or merge the template into one of those settings files. For benchmark runs, prefer the target worktree's `.claude/settings.local.json` so the hook is scoped to that run instead of every Claude Code project.

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

Inside Claude Code, run `/status` to confirm the settings file is loaded. After one prompt or tool call, check `$AI_EVAL_RUN_DIR/events.jsonl` for recorded events.

## What Gets Recorded

Hooks append normalized, redacted events to:

```text
runs/<workflow>/<task-id>/<run-id>/events.jsonl
```

Events keep summaries, not full content:

```text
source, session_id, turn_id, hook_event, model, cwd, tool_name
action.kind, action.command_summary, action.paths, action.success
action.result_summary.observed, empty, result_count, output_chars, line_count
context.type, context.id, context.classification_source
classifications
```

The recorder redacts common API keys, tokens, passwords, bearer tokens, OpenAI-style `sk-*` keys, and JWT-like values. It does not store full prompts, file contents, or large tool output. `result_summary` stores metadata only: whether output was observed, whether it was empty, and small counts. It is used for true hit-rate calculation without preserving tool output.

Context classification is deliberately conservative:

```text
task.json context_sources -> adapter/tool metadata -> path/name heuristic -> unknown
```

Prefer explicit `task.json.context_sources` mappings for benchmark tasks. If a context event cannot be classified safely, it is marked `unknown`; wrong categories are worse than missing categories.

## Derived Fields

Run:

```bash
python -m scripts.summarize_run_events \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

`python -m scripts.collect_run --write` also summarizes automatically when `events.jsonl` exists.

Derived fields include:

```text
model
models_used
duration_minutes
human_interventions
permission_requests
process_evidence.project_instructions_read
process_evidence.relevant_docs_read
process_evidence.knowledge_sources_used
process_evidence.tools_used
process_evidence.self_review_performed
event_collection
```

`duration_minutes` is the coding workflow wall-clock duration from the first `UserPromptSubmit` to the final terminal event. Unknown values stay unknown. The hook layer does not calculate `cost_usd`, hidden test results, adoption rate, link metrics, or whether a plan was semantically followed.

Cross-run link metrics are calculated separately:

```bash
python -m scripts.context_metrics --runs runs --output reports/context-metrics.json
```

That script calculates call rate, hit rate, and adoption rate across runs with non-empty `events.jsonl`.

## Guardrail

During `AI_EVAL_PHASE=coding`, the hook blocks tool calls that touch `acceptance.md`. `task.md` is the coding input; `acceptance.md` is review-only evidence.

This guardrail protects blind review discipline. It is not a sandbox.
