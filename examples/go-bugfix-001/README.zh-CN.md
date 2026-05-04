# Go Bugfix 示例

[English](README.md)

这是一个端到端示例。它展示一次完整评估 run 在任务定义、workflow 执行、证据采集、review 和评分之后应该长什么样。

它不是实时的 `runs/` 目录。本地运行证据应该放在 `runs/` 下，并且默认被 git 忽略。

## 场景

官方 benchmark 任务指向公开 Go demo 仓库：

```text
https://github.com/ZacharyFan/ai-coding-evaluation-demo-golang.git
```

benchmark 任务要求 workflow 修复 `cart.ApplyDiscount`，让它拒绝小于 `0` 或大于 `100` 的非法折扣百分比。

## 文件

```text
task/   benchmark 任务定义的副本
run/    已完成 run 证据的副本
```

run 证据展示：

```text
task.md               本次 run 的英文 coding prompt 快照
task.zh-CN.md         本次 run 的中文 coding prompt 快照
transcript.md         workflow 和目标提交的英文摘要
transcript.zh-CN.md   workflow 和目标提交的中文摘要
events.jsonl          精选、脱敏的 hook 事件，用于派生过程证据
diff.patch            目标项目的最终 diff
test.log              捕获到的测试命令输出
run.json              评分前 run 事实
score.json            review 分、结构化 review 备注和最终分
```

## 复现流程形状

真实本地 run 使用 `runs/`，不是这个示例目录。`prepare_run.py` 会在 workflow 开始前把公开 target repo clone 到 `runs/.../target`，并把 coding task prompt 复制到 run 目录。`acceptance.md` 不会被复制，它只服务 review 阶段。

在这个例子里，`baseline` 只是 workflow 分组标签，用于 run 路径和报告聚合。

```bash
python scripts/prepare_run.py --workflow baseline --task go-bugfix-001 --run-id demo-002
python scripts/execute_run.py \
  --task benchmarks/tasks/go-bugfix-001/task.json \
  --run runs/baseline/go-bugfix-001/demo-002/run.json \
  --write
python scripts/show_solution_diff.py \
  --task benchmarks/tasks/go-bugfix-001/task.json \
  --run runs/baseline/go-bugfix-001/demo-002/run.json \
  --color auto
python scripts/score_run.py \
  --task benchmarks/tasks/go-bugfix-001/task.json \
  --run runs/baseline/go-bugfix-001/demo-002/run.json \
  --score runs/baseline/go-bugfix-001/demo-002/score.json \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6 \
  --write
python scripts/report.py --runs runs
```
