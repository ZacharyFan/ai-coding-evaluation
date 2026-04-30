# AI Coding 工作流评估

[英文版](README.md)

本仓库是一个 AI Coding 工作流测试台，用来在可复跑的工程任务上比较不同工作流的效果。

评估单位不是“AI 有没有写代码”，而是：

```text
accepted change / human attention minute
```

## 仓库结构

```text
benchmarks/tasks/   任务说明、验收标准、检查项和评分权重
workflows/          待比较的工作流定义
runs/               每个工作流、每个任务的运行证据
schemas/            task、workflow、run 文件的 JSON schema
scripts/            创建 run、评分、生成报告的零依赖脚本
tests/              评估工具自身的单元测试
docs/               评估方法和评分规则文档
```

Python、TypeScript、Go、Rust 等目标项目示例见 [docs/multi-language-targets.zh-CN.md](docs/multi-language-targets.zh-CN.md)。

## 第一批校准任务

初始 benchmark 集包含 5 个任务模板：

```text
bugfix-001     修复一个真实缺陷
feature-001    添加一个小功能
refactor-001   在不改变行为的前提下改进结构
test-001       补齐缺失测试覆盖
frontend-001   改进一个 UI 或集成流程
```

这些文件有意保留为模板。真正相信评分之前，先把每个任务里的 `task.md`、`acceptance.md` 和 `tests.sh` 换成真实代码仓库里的具体任务。

## 快速开始

创建一次运行的证据目录：

```bash
python scripts/run_task.py --workflow baseline --task bugfix-001
```

给一次运行评分：

```bash
python scripts/score_run.py \
  --task benchmarks/tasks/bugfix-001/task.json \
  --run runs/baseline/bugfix-001/latest/metrics.json \
  --write
```

生成汇总报告：

```bash
python scripts/report.py --runs runs
```

运行测试：

```bash
pytest
```

## 硬门槛

硬门槛会限制最终得分上限，防止“很快但不可靠”的工作流看起来很好。

```text
task_not_solved          最高 40 分
security_issue           最高 50 分
public_api_break         最高 55 分
required_tests_failed    最高 60 分
unrelated_changes        最高 65 分
hidden_tests_failed      最高 70 分
```

## 决策规则

5 个任务只适合校准 benchmark 本身。10-15 个任务可以淘汰明显差的工作流。30 个以上任务才适合选择主力工作流。
