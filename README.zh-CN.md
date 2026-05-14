# AI Coding 工作流评估

[英文版](README.md)

这个仓库是一个可复跑 benchmark，用真实工程任务比较不同 AI Coding workflow 的效果。

这不是 agent 框架，也不是模型排行榜；它是一个在可复跑工程任务上比较 AI Coding workflow 的评估协议。

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

## 心智模型

```text
task.json + task.md + acceptance.md
        ->
prepare_run 创建隔离 target worktree
        ->
AI/人工 coding 修改 runs/.../target
        ->
collect_run 采集测试、diff 和 scope 事实
        ->
人工 review 或 llm_review_run 写入 score.json
        ->
report/dashboard 对比 workflows 和 models
```

```text
task      = 可复用的 benchmark 用例
run       = 某个 workflow/model 在某个 task 上的一次尝试
score     = 这次 run 的 review 结果
dashboard = 只读的对比投影
```

## 快速开始

先在 `benchmarks/tasks/` 下添加一个公开可复跑任务，然后用快捷 CLI 走最短评分闭环。

1. 准备一次 run：

```bash
python -m scripts.eval start --workflow <workflow> --task <task-id> [--model <model>]
```

<details>
<summary><strong>可选：</strong>采集 hook 过程证据</summary>

启动 Claude Code 或 Codex 前，先导出当前 run 环境：

```bash
eval "$(python -m scripts.eval env)"
python -m scripts.eval hooks
```

安装脚本会把 run-scoped Codex 和 Claude Code hook 文件写入当前 target worktree，并加入该 worktree 的本地 git exclude。

如果未被 git 跟踪的 hook 文件已经存在，使用：

```bash
python -m scripts.eval hooks --merge
```

它会追加评估 recorder hook，并避免重复命令。已被 target repo 跟踪的 hook 文件永远不会被修改。

agent 必须从同一个 shell 启动，才能继承 `AI_EVAL_*`。如果你不在 evaluation 仓库根目录，先执行：

```bash
eval "$(/absolute/path/to/ai-coding-evaluation/bin/ai-eval env)"
```

然后回到 evaluation 仓库执行 `python -m scripts.eval hooks`。

Hooks 会增强 `process_evidence` 和链路指标，但不影响完成一次基础评分闭环。详见 [docs/hooks.zh-CN.md](docs/hooks.zh-CN.md)。

</details>

然后进入 target worktree：

```bash
cd "$AI_EVAL_TARGET_WORKTREE"
```

AI 或人工 workflow 修改准备好的 target worktree。Coding prompt 使用复制到 run 目录下的 `task.md`；如果偏好中文，使用 `task.zh-CN.md`。`acceptance.md` 继续只留在 benchmark task 目录中，供 review 阶段使用。

2. coding 完成后，采集测试和 diff 证据：

```bash
python -m scripts.eval collect
```

<details>
<summary><strong>可选：</strong>计算采纳率指标</summary>

如果要计算行级采纳率，让 AI workflow 或 reviewer 先把 candidate 结果提交成 commit，再把这个 candidate commit 与最终采纳 commit 对比。这个指标只用于链路诊断，不影响 `score.json`。

```bash
cd runs/<workflow>/<task-id>/<run-id>/target
git add .
git commit -m "candidate for <task-id>"
git rev-parse HEAD
```

最终采纳版本也形成 commit 后：

```bash
python -m scripts.eval adoption \
  --candidate-ref <candidate-sha> \
  --accepted-ref <accepted-sha>
```

`candidate_ref` 是 AI candidate commit。`accepted_ref` 是最终采纳 commit。`target.solution_ref` 仍然只是参考解，不作为默认采纳来源。

</details>

<details>
<summary><strong>可选：</strong>查看参考解 diff</summary>

如果任务配置了 `target.solution_ref`，可以在打分前查看候选 worktree 与参考实现之间的 diff。这个 helper 会在存在 `task.scope.allowed_paths` 时只展示任务允许范围内的差异，输出带文件标题和行号的 reviewer-friendly diff view，并用红色背景标记候选侧行、绿色背景标记参考侧行。

```bash
python -m scripts.eval solution-diff --color auto
```

它只给 reviewer 提供上下文，不能按“和参考解相似度”打分。

</details>

3. 正式计算分数前，先选择一种 review 路径。

人工路径，首次运行推荐使用：直接传入六个 review 分数。这会创建或更新 `score.json`，并一次性计算最终分。每个 review 值必须在 `0.0` 到 `1.0` 之间。除非 reviewer 明确要压分，否则不要传 `--manual-hard-gate`：

```bash
python -m scripts.eval score \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6
```

如果需要人工 hard gate，追加 `--manual-hard-gate public_api_break`。`python -m scripts.eval score --init` 仍然保留给偏好手动编辑 draft JSON 的 reviewer。

LLM review 路径：用 OpenAI-compatible reviewer 自动生成 `score.json` 并一次性计算最终分：

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
python -m scripts.eval llm-review
```

如果使用 DeepSeek-compatible review，把 `AI_EVAL_REVIEW_BASE_URL` 设为 `https://api.deepseek.com`，并传入 `--api-key-env DEEPSEEK_API_KEY`。

4. 生成报告或看板：

```bash
python -m scripts.eval report
python -m scripts.eval dashboard
python -m scripts.eval registry
```

`report.py` 是快速终端/Markdown 报告。`dashboard.py` 是只读可视化对比看板，用来比较 workflow、model、同任务结果和链路指标。它会同时写入 `reports/dashboard.html` 和 `reports/dashboard.zh-CN.html`，不会修改 `run.json`、`score.json` 或 review 结果。

`benchmark_registry.py` 会生成双语任务索引：`benchmarks/index.html` 和 `benchmarks/index.zh-CN.html`。它是 `benchmarks/tasks/` 下可执行任务的语言无关目录，只展示任务 metadata 和入口，不展示 run 结果。

<details>
<summary><strong>可选：</strong>生成链路指标</summary>

从 hook 证据生成跨 run 链路指标：

```bash
python -m scripts.context_metrics --runs runs --output reports/context-metrics.json
```

这是跨 run 诊断视图，不参与评分。链路指标依赖 hook events；没有非空 `events.jsonl` 的 run 不计入分母。

</details>

这个快捷 CLI 不引入新的评估协议。它只是把最近一次 run 记在 `runs/.current.json`，并自动解析 `task.json`、`run.json` 和 `score.json` 路径。并行跑多个实验时，对 `collect`、`score`、`llm-review`、`solution-diff` 或 `adoption` 传入 `--run-dir runs/<workflow>/<task-id>/<run-id>` 即可。

## 底层命令

快捷 CLI 只是稳定原语上的薄封装。调试、CI 或不想使用 `runs/.current.json` 时，可以直接运行底层命令：

```bash
python -m scripts.prepare_run --workflow <workflow> --task <task-id> [--model <model>]
python -m scripts.collect_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python -m scripts.score_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --score runs/<workflow>/<task-id>/<run-id>/score.json --set-review correctness=1.0 regression_safety=1.0 maintainability=0.8 test_quality=0.8 security=1.0 process_compliance=0.6 --write
python -m scripts.llm_review_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python -m scripts.report --runs runs
python -m scripts.dashboard --runs runs --tasks benchmarks/tasks --output reports/dashboard.html
python -m scripts.benchmark_registry --tasks benchmarks/tasks --output benchmarks/index.html
```

完整端到端样例见 [examples/go-bugfix-l1-c1](examples/go-bugfix-l1-c1)。

## 贡献评估用例

有价值的公开 benchmark 用例：

- 来自真实工程变更
- 使用固定的公开 target repo 和 base commit
- 定义清晰的期望行为
- 能通过可复跑命令验证
- 避免私有数据、凭据和只能在本机运行的环境

避免：

- 玩具算法题
- 模糊的产品需求
- 只能在某个人电脑上运行的任务
- 把答案泄露到 `task.md`
- 没有可复跑测试或 review 信号的任务

复制最接近的任务类型模板：

```bash
cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
```

然后修改 `task.json`，尤其是 `target`、可选的 `target.solution_ref` 和 `scope.allowed_paths`，以及 `task.md`、`acceptance.md` 和 `tests.sh`。

开 PR 前运行：

```bash
python -m scripts.validate_task benchmarks/tasks/<task-id>
ruff check scripts tests
ruff format --check scripts tests
python -m pytest
```

PR 流程见 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。如何写好用例见 [docs/task-authoring.zh-CN.md](docs/task-authoring.zh-CN.md)。

## 维护与贡献检查

修改 benchmark 任务、模板、schema、脚本或文档时运行：

```bash
python -m scripts.validate_task
python -m scripts.eval registry
ruff check scripts tests
ruff format --check scripts tests
python -m pytest
```

这些命令验证评估仓库本身是否健康。它们是维护和贡献门禁，不是单次 workflow run 的评分路径。

## 仓库结构

```text
benchmarks/tasks/       参与运行和报告统计的真实 benchmark 任务
benchmarks/index.html   生成的双语任务索引入口
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
