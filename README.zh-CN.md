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
- review 和效率评分权重

每个 workflow 从同一个起点运行同一个任务。一次 run 会在 `runs/` 里保留证据：交互记录、diff、测试日志、review 记录和标准化指标。评分器先结合盲审维度和效率，再用 hard gates 限制不安全或未完成工作的最终分。

## 快速开始

先在 `benchmarks/tasks/` 下添加一个真实任务，然后创建一次 run 的证据目录：

```bash
python scripts/run_task.py --workflow baseline --task <task-id>
```

给一次 run 评分：

```bash
python scripts/score_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/baseline/<task-id>/latest/metrics.json \
  --write
```

生成汇总报告：

```bash
python scripts/report.py --runs runs
```

验证 benchmark 任务和工具链：

```bash
python scripts/validate_task.py
pytest
```

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

## 仓库结构

```text
benchmarks/tasks/       参与运行和报告统计的真实 benchmark 任务
benchmarks/templates/   可复制的用例编写模板，默认不运行
workflows/              待比较的 workflow 定义
runs/                   每个 workflow、每个任务的运行证据
schemas/                task、workflow、run 文件的 JSON schema
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

真实任务放在 `benchmarks/tasks/`。模板保留在 `benchmarks/templates/`，不参与默认运行和报告统计。

决策置信度：

```text
5 个任务      80% 适合调试 benchmark，30% 适合选择 workflow
10-15 个任务  60% 适合淘汰弱 workflow
30+ 个任务    75% 适合选择主力 workflow
```
