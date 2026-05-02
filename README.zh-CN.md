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

- 固定的目标仓库和 `base_ref`
- 任务提示词、验收标准、必跑检查和 hidden review checks
- 时间、人类介入和成本预算
- 工作量与复杂度元数据
- review 和效率的 `scoring_weights`

每个 workflow 从同一个起点运行同一个任务。公开任务指向可 clone 的目标仓库和固定 commit SHA。一次 run 会把事实记录在 `run.json`，把评分结果记录在 `score.json`，旁边保留交互记录、diff 和测试日志证据。

`--workflow` 是对比用的分组标签，不是协议文件。可以用任意稳定标签聚合 runs，例如 `baseline`、`codex`、`claude`、`plan-first`、`tdd`。真正的执行过程由操作者、`transcript.md`、`run.json.process_evidence` 和运行证据记录。

## 快速开始

先在 `benchmarks/tasks/` 下添加一个公开可复跑任务，然后准备隔离 target worktree：

```bash
python scripts/prepare_run.py --workflow <workflow> --task <task-id>
```

AI 或人工 workflow 修改准备好的 `runs/.../target` worktree 后，采集测试和 diff 证据：

```bash
python scripts/execute_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

人工 review 时，先初始化待填写的 `score.json`，填完 review 分后再计算最终评分字段：

```bash
python scripts/score_run.py \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --score runs/<workflow>/<task-id>/<run-id>/score.json \
  --init \
  --write

python scripts/score_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --score runs/<workflow>/<task-id>/<run-id>/score.json \
  --write
```

也可以用 OpenAI-compatible LLM reviewer 自动生成 `score.json`：

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
python scripts/llm_review_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

如果使用 DeepSeek-compatible review，把 `AI_EVAL_REVIEW_BASE_URL` 设为 `https://api.deepseek.com`，并传入 `--api-key-env DEEPSEEK_API_KEY`。

生成汇总报告：

```bash
python scripts/report.py --runs runs
```

完整端到端样例见 [examples/go-bugfix-001](examples/go-bugfix-001)。

## 贡献评估用例

复制最接近的任务类型模板：

```bash
cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
```

然后修改 `task.json`、`task.md`、`acceptance.md` 和 `tests.sh`。

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
examples/               可提交的精选任务和运行证据样例
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
