# 基于 Hook 的过程证据采集

[英文版](hooks.md)

Hook 是可选的过程证据层，用来记录 coding 过程中发生了什么。它不负责评分，也不替代 `python -m scripts.collect_run`。

整体形态刻意保持简单：

```text
Claude/Codex hook input -> record_hook_event.py -> events.jsonl -> summarize_run_events.py -> run.json
```

## 配置

先准备一次 run：

```bash
python -m scripts.eval start --workflow <workflow> --task <task-id> [--model <model>]
```

启动 coding agent 前，先导出当前 run 环境：

```bash
eval "$(python -m scripts.eval env)"
python -m scripts.eval hooks
```

如果你不在 evaluation 仓库根目录，改用这个薄 wrapper：

```bash
eval "$(/absolute/path/to/ai-coding-evaluation/bin/ai-eval env)"
cd "$AI_EVAL_REPO"
python -m scripts.eval hooks
```

`scripts.eval env` 会输出绝对路径，所以导出的环境变量在 `cd` 到 target worktree 后仍然有效。
`python -m scripts.eval hooks` 会把 Codex 和 Claude Code hook 文件写入准备好的 target worktree，并加入该 worktree 的本地 `.git/info/exclude`。如果 hook 文件已经被 target repo 跟踪，它会拒绝修改。

然后从同一个 shell 启动 Claude Code 或 Codex：

```bash
cd "$AI_EVAL_TARGET_WORKTREE"
```

agent 必须在 `eval` 之后启动，hook 进程才能继承 `AI_EVAL_REPO`、`AI_EVAL_RUN_DIR`、`AI_EVAL_TARGET_WORKTREE` 和 `AI_EVAL_PHASE`。环境变量不会 retroactively 影响已经启动的 Codex 或 Claude session。

Coding prompt 使用复制到 run 目录下的任务文件：`runs/<workflow>/<task-id>/<run-id>/task.md`；如果偏好中文，使用 `task.zh-CN.md`。`acceptance.md` 是 reviewer-only 文件，不会复制到 run 目录。

## Codex

Codex hooks 需要开启 feature flag：

```toml
[features]
codex_hooks = true
```

`python -m scripts.eval hooks` 会把 `integrations/codex/config.example.toml` 和 `integrations/codex/hooks.example.json` 安装到当前 target worktree。hook command 会使用 `$AI_EVAL_REPO`，所以启动 Codex 前必须先执行 `eval "$(python -m scripts.eval env)"`；如果不在仓库根目录，就用 `bin/ai-eval env`。

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

`python -m scripts.eval hooks` 会把 `integrations/claude-code/settings.example.json` 安装到当前 target worktree 的 `.claude/settings.local.json`。Claude Code settings 可以放在：

```text
~/.claude/settings.json
.claude/settings.json
.claude/settings.local.json
```

benchmark run 场景下，优先放到 target worktree 的 `.claude/settings.local.json`，这样 hook 只作用于当前 run，不会污染所有 Claude Code 项目。如果需要和已有项目级 Claude settings 合并，手动合并，并且不要把 secret 写进可提交文件。

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

在 Claude Code 中运行 `/status` 可以确认 settings 文件已加载。触发一次 prompt 或 tool call 后，检查 `$AI_EVAL_RUN_DIR/events.jsonl` 是否出现记录。

## 记录什么

Hook 会把标准化、脱敏后的事件追加到：

```text
runs/<workflow>/<task-id>/<run-id>/events.jsonl
```

事件只保留摘要，不保留完整内容：

```text
source, session_id, turn_id, hook_event, model, cwd, tool_name
action.kind, action.command_summary, action.paths, action.success
action.result_summary.observed, empty, result_count, output_chars, line_count
context.type, context.id, context.classification_source
classifications
```

采集器会脱敏常见 API key、token、password、bearer token、OpenAI 风格的 `sk-*` key 和 JWT-like 值。它不保存完整 prompt、文件内容或大段工具输出。`result_summary` 只保存元数据：是否观测到输出、是否为空，以及少量计数。它用于计算真命中率，不保存工具输出正文。

context 分类保持保守：

```text
task.json context_sources -> adapter/tool metadata -> path/name heuristic -> unknown
```

benchmark 任务优先配置 `task.json.context_sources`。无法安全分类时标记为 `unknown`；错分比缺失更危险。

## 派生字段

运行：

```bash
python -m scripts.summarize_run_events \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

`python -m scripts.collect_run --write` 发现 `events.jsonl` 时也会自动汇总一次。

会自动派生：

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

`duration_minutes` 是 coding workflow 从第一条 `UserPromptSubmit` 到最后一个终止事件的墙钟耗时。未知值继续保持未知。hook 层不计算 `cost_usd`、hidden test 结果、采纳率、链路指标，也不猜测 plan 是否被语义上遵循。

跨 run 链路指标由独立脚本计算：

```bash
python -m scripts.context_metrics --runs runs --output reports/context-metrics.json
```

该脚本只统计有非空 `events.jsonl` 的 run，并计算调用率、命中率和采纳率。

## 护栏

在 `AI_EVAL_PHASE=coding` 阶段，hook 会阻止触碰 `acceptance.md` 的工具调用。`task.md` 是 coding 输入，`acceptance.md` 是 review-only evidence。

这个护栏保护 blind review 纪律。它不是 sandbox。
