# 基于 Hook 的过程证据采集

[英文版](hooks.md)

Hook 是可选的过程证据层，用来记录 coding 过程中发生了什么。它不负责评分，也不替代 `execute_run.py`。

整体形态刻意保持简单：

```text
Claude/Codex hook input -> record_hook_event.py -> events.jsonl -> summarize_run_events.py -> run.json
```

## 配置

先准备一次 run：

```bash
python scripts/prepare_run.py --workflow <workflow> --task <task-id>
```

启动 coding agent 前，导出 `prepare_run.py` 打印的运行环境：

```bash
export AI_EVAL_REPO=/path/to/ai-coding-evaluation
export AI_EVAL_RUN_DIR=/path/to/ai-coding-evaluation/runs/<workflow>/<task-id>/<run-id>
export AI_EVAL_TARGET_WORKTREE=$AI_EVAL_RUN_DIR/target
export AI_EVAL_PHASE=coding
```

然后从准备好的 target worktree 启动 Claude Code 或 Codex：

```bash
cd "$AI_EVAL_TARGET_WORKTREE"
```

Coding prompt 使用 `$AI_EVAL_RUN_DIR/task.md`；如果偏好中文，使用 `$AI_EVAL_RUN_DIR/task.zh-CN.md`。`acceptance.md` 是 reviewer-only 文件，不会复制到 run 目录。

## Codex

Codex hooks 需要开启 feature flag：

```toml
[features]
codex_hooks = true
```

可以把 `integrations/codex/config.example.toml` 和 `integrations/codex/hooks.example.json` 复制到 `~/.codex/config.toml`、`~/.codex/hooks.json`，也可以放到项目本地 `.codex/` 配置中。

模板会记录：

```text
SessionStart
UserPromptSubmit
PreToolUse
PermissionRequest
PostToolUse
Stop
```

Codex hook 的覆盖很有价值，但不是安全边界。当前 Codex hooks 不能拦截所有 shell 或 web 路径，所以它是“过程证据 + 轻量护栏”，不是 sandbox。

## Claude Code

可以把 `integrations/claude-code/settings.example.json` 作为 Claude Code settings 的模板。

模板会记录：

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

Claude 的 `InstructionsLoaded` 事件能更可靠地判断项目规范是否被加载，比单纯从文件读取事件推断更稳。

## 记录什么

Hook 会把标准化、脱敏后的事件追加到：

```text
runs/<workflow>/<task-id>/<run-id>/events.jsonl
```

事件只保留摘要，不保留完整内容：

```text
source, session_id, turn_id, hook_event, model, cwd, tool_name
action.kind, action.command_summary, action.paths, action.success
classifications
```

采集器会脱敏常见 API key、token、password、bearer token、OpenAI 风格的 `sk-*` key 和 JWT-like 值。它不保存完整 prompt、文件内容或大段工具输出。

## 派生字段

运行：

```bash
python scripts/summarize_run_events.py \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

`execute_run.py --write` 发现 `events.jsonl` 时也会自动汇总一次。

会自动派生：

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

未知值继续保持未知。hook 层不计算 `cost_usd`、hidden test 结果、采纳率，也不猜测 plan 是否被语义上遵循。

## 护栏

在 `AI_EVAL_PHASE=coding` 阶段，hook 会阻止触碰 `acceptance.md` 的工具调用。`task.md` 是 coding 输入，`acceptance.md` 是 review-only evidence。

这个护栏保护 blind review 纪律。它不是 sandbox。
