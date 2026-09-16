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

## 为什么不是模型排行榜？

模型排行榜回答的是“哪个模型在固定测试上分更高”。这个项目回答的是更接近工程现场的问题：

```text
在我的真实任务分布上，哪个 workflow 能用最少的人类注意力产出可接受代码？
```

这个 benchmark 会把质量证据、过程证据和交付证据分开。更强的模型也可能输：如果 workflow 需要持续人工纠偏、跳过项目上下文，或者产出的改动无法通过 review，它就不便宜。

## 仓库里有什么

- `benchmarks/tasks/` 下 36 个可执行 Go benchmark 任务
- `benchmarks/templates/` 下可复制的任务模板
- `examples/go-bugfix-l1-c1/` 下一个已评分的端到端 demo
- `scripts/` 下零运行时依赖的 Python CLI helper
- `integrations/` 下可选 Codex 和 Claude Code hook 模板
- 中英文文档、schema、报告和 dashboard 生成器

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

## 安装

CLI 和 demo 的基础要求：

```text
Python 3.11+
Git
```

从 checkout 安装：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ai-eval doctor
```

所有 `ai-eval ...` 命令也可以在仓库根目录写成 `python -m scripts.eval ...`。`bin/ai-eval` 继续保留，适合需要绝对 repo helper 的 shell 流程。

## 快速开始

### 2 分钟 demo

这条路径不需要 API key，也不需要真实 AI coding session。它会把已提交的评分样例复制到本地 ignored `runs/` 证据目录，然后生成正常的 report 和 dashboard。

```bash
ai-eval demo
ai-eval report --runs runs
ai-eval dashboard --runs runs --tasks benchmarks/tasks
```

打开 `reports/dashboard.html` 或 `reports/dashboard.zh-CN.html` 查看可视化看板。Demo 是幂等的；用 `ai-eval demo --reset` 重建 `runs/demo/go-bugfix-l1-c1/example`。

### 10 分钟真实 run

要求：Git、Python 3.11+、Go。

```bash
ai-eval start --workflow baseline --task go-bugfix-l1-c1 --model <model>
eval "$(ai-eval env)"
cd "$AI_EVAL_TARGET_WORKTREE"
```

在 target worktree 中运行你的 AI 或人工 workflow。Coding prompt 使用复制到 run 目录下的 `task.md`；如果偏好中文，使用 `task.zh-CN.md`。`acceptance.md` 继续留在 benchmark task 目录中，只供 review 阶段使用。

Coding 完成后：

```bash
ai-eval collect
ai-eval score \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6
ai-eval report --runs runs
ai-eval dashboard --runs runs --tasks benchmarks/tasks
```

### 贡献一个任务

```bash
cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
python -m scripts.validate_task benchmarks/tasks/bugfix-002
ai-eval registry
ruff check scripts tests
ruff format --check scripts tests
python -m pytest
```

PR 流程见 [CONTRIBUTING.zh-CN.md](CONTRIBUTING.zh-CN.md)。如何写好用例见 [docs/task-authoring.zh-CN.md](docs/task-authoring.zh-CN.md)。

## 高级证据

这些可选证据路径用于更深入的过程、review 或对比分析，不再压到 Quick Start 默认阅读流里。

<details>
<summary><strong>可选：</strong>用成对 Δ 对比 workflows</summary>

当两个 workflow 在相同任务上都有已评分 run 时，report 会输出成对汇总，把每个 workflow 与参考 workflow 逐一相减：

```bash
ai-eval report --runs runs --reference-workflow baseline
```

```text
Paired vs reference workflow: baseline

| Workflow | Pairs | Arm Coverage | Mean Score Delta | Sign Consistency |
| plan-first | 4 | 4/5 | +3.20 | 0.75 |
```

按 (任务, 模型) 把候选与参考两侧的分数各自聚成臂再相减。任务难度在同一对内自动抵消，Δ 只反映 workflow 差异，不再混入任务方差。`Mean Score Delta` 是幅度；`Sign Consistency` 是同方向 pair 的占比（任务数少时依然稳健）；`Arm Coverage` 表示多少候选臂找到了配对的参考臂。

要让配对成立，两个 workflow 需在相同任务集上用相同模型运行，并交替顺序（A/B/A/B），让时间漂移均摊到两侧。任务或模型在参考侧找不到对应臂时，该臂计入 coverage 分母但不产出 pair。传入 `--no-paired` 可跳过该段落。

</details>

<details>
<summary><strong>可选：</strong>启动 run 前浏览可用任务</summary>

想在选择 run 前浏览任务 metadata，可以生成双语任务索引：

```bash
ai-eval registry
```

`benchmark_registry.py` 会写入 `benchmarks/index.html` 和 `benchmarks/index.zh-CN.html`。它是 `benchmarks/tasks/` 下可执行任务的语言无关目录，只展示任务 metadata 和入口，不展示 run 结果。

</details>

<details>
<summary><strong>可选：</strong>采集 hook 过程证据</summary>

Hook 证据会增强 `process_evidence` 和上下文链路指标。启动 Claude Code 或 Codex 前：

```bash
eval "$(ai-eval env)"
ai-eval hooks
```

如果已有未被 git 跟踪的 hook 文件，使用 `ai-eval hooks --merge`。已被 target repo 跟踪的 hook 文件永远不会被修改。

agent 必须从同一个 shell 启动，才能继承 `AI_EVAL_*`。Hooks 会增强证据，但不影响完成一次基础评分闭环。详见 [docs/hooks.zh-CN.md](docs/hooks.zh-CN.md)。

</details>

<details>
<summary><strong>可选：</strong>计算采纳率指标</summary>

如果要计算行级采纳率，让 workflow 或 reviewer 先把 candidate 结果提交成 commit，再把这个 candidate commit 与最终采纳 commit 对比：

```bash
ai-eval adoption --candidate-ref <candidate-sha> --accepted-ref <accepted-sha>
```

`candidate_ref` 是 AI candidate commit。`accepted_ref` 是最终采纳 commit。`target.solution_ref` 仍然只是参考解，不作为默认采纳来源。

</details>

<details>
<summary><strong>可选：</strong>查看参考解 diff</summary>

如果任务配置了 `target.solution_ref`，可以在打分前查看候选 worktree 与参考实现之间的 diff：

```bash
ai-eval solution-diff --color auto
```

它只给 reviewer 提供上下文，不能按“和参考解相似度”打分。

</details>

<details>
<summary><strong>可选：</strong>使用 LLM review</summary>

LLM review 可以用 OpenAI-compatible reviewer 自动生成 `score.json`：

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
ai-eval llm-review
```

如果使用 DeepSeek-compatible review，把 `AI_EVAL_REVIEW_BASE_URL` 设为 `https://api.deepseek.com`，并传入 `--api-key-env DEEPSEEK_API_KEY`。

</details>

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

<details>
<summary>展开底层原语命令</summary>

```bash
python -m scripts.prepare_run --workflow <workflow> --task <task-id> [--model <model>]
python -m scripts.collect_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python -m scripts.score_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --score runs/<workflow>/<task-id>/<run-id>/score.json --set-review correctness=1.0 regression_safety=1.0 maintainability=0.8 test_quality=0.8 security=1.0 process_compliance=0.6 --write
python -m scripts.llm_review_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python -m scripts.report --runs runs
python -m scripts.dashboard --runs runs --tasks benchmarks/tasks --output reports/dashboard.html
python -m scripts.benchmark_registry --tasks benchmarks/tasks --output benchmarks/index.html
```

</details>

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

当前仓库同时提供可执行 Go benchmark 任务和任务类型模板：

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
