# AI Coding 工作流评估

[英文版](README.md)

这个仓库是一个可复跑 benchmark，用真实工程任务比较不同 AI Coding workflow 的效果。

核心问题不是“AI 会不会写代码”，而是：

```text
哪个 workflow 能用最少的人类注意力产出可接受变更？
```

主评估单位是：

```text
accepted change / human attention minute
```

## 它如何工作

每个 benchmark task 会定义：

- 固定的目标仓库、`base_ref` 和可选的参考用 `solution_ref`
- 任务提示词、验收标准、必跑检查和 hidden review checks
- 时间、人类介入和成本预算
- 工作量与复杂度元数据
- review 和效率的 `scoring_weights`

每个 workflow 从同一个起点运行同一个任务。公开任务指向可 clone 的目标仓库和固定 commit SHA。可选的 `target.solution_ref` 是给作者和 reviewer 参考的官方参考实现；它不是唯一正确答案，也不会被工具链使用。一次 run 会把事实记录在 `run.json`，把评分结果记录在 `score.json`，旁边保留交互记录、diff 和测试日志证据。

`--workflow` 是对比用的分组标签，不是协议文件。它应该表达流程标签，例如 `baseline`、`plan-first`、`tdd`。模型身份写入 `run.json.model`，例如 `gpt-5.5` 或 `claude-sonnet-4.5`；不要把模型名混进 `workflow_id`。真正的执行过程由操作者、`transcript.md`、`run.json.process_evidence` 和运行证据记录。

## 快速开始

先在 `benchmarks/tasks/` 下添加一个公开可复跑任务，然后准备隔离 target worktree：

```bash
python scripts/prepare_run.py --workflow <workflow> --task <task-id> --model <model>
```

AI 或人工 workflow 修改准备好的 `runs/.../target` worktree。Coding prompt 使用 `runs/<workflow>/<task-id>/<run-id>/task.md`；如果偏好中文，使用 `task.zh-CN.md`。`acceptance.md` 继续只留在 benchmark task 目录中，供 review 阶段使用。

如果要用 Claude Code 或 Codex hook 自动采集过程证据，先导出 `prepare_run.py` 打印的 `AI_EVAL_*` 变量，再从 `runs/.../target` 启动 agent。详见 [docs/hooks.zh-CN.md](docs/hooks.zh-CN.md)。

coding 完成后，采集测试和 diff 证据：

```bash
python scripts/execute_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

可选 review 辅助：如果任务配置了 `target.solution_ref`，可以在打分前查看候选 worktree 与参考实现之间的 diff。这个 helper 会在存在 `task.scope.allowed_paths` 时只展示任务允许范围内的差异，输出带文件标题和行号的 reviewer-friendly diff view，并用红色背景标记候选侧行、绿色背景标记参考侧行。它只给 reviewer 提供上下文，不能按“和参考解相似度”打分。

```bash
python scripts/show_solution_diff.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --color auto
```

正式计算分数前，先二选一完成 review。

人工路径：直接传入六个 review 分数。这会创建或更新 `score.json`，并一次性计算最终分。每个 review 值必须在 `0.0` 到 `1.0` 之间。除非 reviewer 明确要压分，否则不要传 `--manual-hard-gate`：

```bash
python scripts/score_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --score runs/<workflow>/<task-id>/<run-id>/score.json \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6 \
  --write
```

如果需要人工 hard gate，追加 `--manual-hard-gate public_api_break`。`score_run.py --init` 仍然保留给偏好手动编辑 draft JSON 的 reviewer。

LLM 路径：用 OpenAI-compatible reviewer 自动生成 `score.json` 并一次性计算最终分：

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
python scripts/llm_review_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

如果使用 DeepSeek-compatible review，把 `AI_EVAL_REVIEW_BASE_URL` 设为 `https://api.deepseek.com`，并传入 `--api-key-env DEEPSEEK_API_KEY`。

生成终端汇总报告：

```bash
python scripts/report.py --runs runs
```

生成静态对比看板：

```bash
python scripts/dashboard.py --runs runs --tasks benchmarks/tasks --output reports/dashboard.html
```

`report.py` 是快速终端/Markdown 报告。`dashboard.py` 是只读可视化对比看板，用来比较 workflow、model 和同任务结果。它会同时写入 `reports/dashboard.html` 和 `reports/dashboard.zh-CN.html`，不会修改 `run.json`、`score.json` 或 review 结果。

完整端到端样例见 [examples/go-bugfix-001](examples/go-bugfix-001)。

## 贡献评估用例

复制最接近的任务类型模板：

```bash
cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
```

然后修改 `task.json`，尤其是 `target`、可选的 `target.solution_ref` 和 `scope.allowed_paths`，以及 `task.md`、`acceptance.md` 和 `tests.sh`。

开 PR 前运行：

```bash
python scripts/validate_task.py benchmarks/tasks/<task-id>
pytest
```

PR 流程见 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。如何写好用例见 [docs/task-authoring.zh-CN.md](docs/task-authoring.zh-CN.md)。

## 维护与贡献检查

修改 benchmark 任务、模板、schema、脚本或文档时运行：

```bash
python scripts/validate_task.py
pytest
```

这些命令验证评估仓库本身是否健康。它们是维护和贡献门禁，不是单次 workflow run 的评分路径。

## 仓库结构

```text
benchmarks/tasks/       参与运行和报告统计的真实 benchmark 任务
benchmarks/local/       私有本地实验任务，git 默认忽略
benchmarks/templates/   可复制的用例编写模板，默认不运行
runs/                   本地运行证据和 target worktree，git 默认忽略
reports/                本地生成的看板和报告，git 默认忽略
examples/               可提交的精选任务和运行证据样例
integrations/           可选的 Claude Code 和 Codex hook 模板
schemas/                task、run、score 文件的 JSON schema
scripts/                校验、评分、报告生成的零依赖脚本
tests/                  评估工具自身的单元测试
docs/                   评估方法、评分规则和用例编写文档
```

## 评分模型

默认加权分：

```text
correctness          35
regression_safety    15
maintainability      15
test_quality         10
security             10
process_compliance    5
efficiency           10
```

Hard gates 会限制最终分数上限：

```text
task_not_solved          最高 40
security_issue           最高 50
public_api_break         最高 55
required_tests_failed    最高 60
unrelated_changes        最高 65
hidden_tests_failed      最高 70
```

指标模型见 [docs/evaluation-method.zh-CN.md](docs/evaluation-method.zh-CN.md)，review 打分见 [docs/rubric.zh-CN.md](docs/rubric.zh-CN.md)。

## 任务类型模板

当前仓库提供的是任务类型模板，不是真实 benchmark 任务：

```text
bugfix      修复一个真实缺陷
feature     添加一个小功能
refactor    在不改变行为的前提下改进结构
test        补齐缺失测试覆盖
frontend    改进一个 UI 或集成流程
```

公开可复跑任务放在 `benchmarks/tasks/`，必须使用可 clone 的 Git URL 和完整 commit SHA。私有或本地实验任务放在 `benchmarks/local/`。模板保留在 `benchmarks/templates/`，不参与默认运行和报告统计。

决策置信度：

```text
5 个任务      80% 适合调试 benchmark，30% 适合选择 workflow
10-15 个任务  60% 适合淘汰弱 workflow
30+ 个任务    75% 适合选择主力 workflow
```
