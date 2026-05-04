# 评估方法

[英文版](evaluation-method.md)

## 修正后的问题

真正有用的问题是：

```text
在我的真实任务分布上，哪个工作流能以最低总成本产出可接受代码？
```

## 主指标

```text
attention_adjusted_score = final_score / max(1, human_interventions)
```

这个指标故意很硬。一个需要人不断介入的工作流并不便宜，即使模型调用费用很低。

## 评分公式

```text
final_score =
  0.35 * correctness
+ 0.15 * regression_safety
+ 0.15 * maintainability
+ 0.10 * test_quality
+ 0.10 * security
+ 0.05 * process_compliance
+ 0.10 * efficiency
```

每个维度先归一化到 `0.0-1.0`，再转换成 `0-100` 分。

## 三层证据模型

AI Coding 评估不能停在“会话里看起来不错”。有用的评估要拆成三层：

```text
quality   离线质量：这次 run 是否安全地解决了任务？
process   过程链路：agent 是否用了正确的项目上下文？
outcome   交付结果：AI 生成代码是否进入了最终可接受变更？
```

本仓库 v0.2 默认评估 quality。process 通过 `process_compliance` 和 run 证据字段记录。outcome 先只保留 adoption 字段，不实现生产采纳率计算。

## 复杂度矩阵

`effort_size` 和任务复杂度正交：

```text
effort_size          活大不大，预算压力高不高？
business_complexity  业务、状态、交互、推理结构难不难？
context_maturity     文档、API、示例、知识库上下文够不够？
```

典型组合：

```text
small + L3_complex        很小但很刁钻
large + L1_standardized   量大但机械
medium + L2_linked        常见真实工程任务
```

复杂度矩阵用于聚合热力图、定位 AI 能力边界：

```text
L1_standardized  标准 CRUD、简单表单、直接 bugfix、简单配置
L2_linked        字段联动、多步骤流程、多表逻辑、集成任务
L3_complex       深度定制 UI、架构级改动、复杂数据流

C1_complete      文档、API、示例、项目知识足够
C2_partial       上下文存在，但不完整、过时或分散
C3_missing       agent 需要推断或补齐缺失上下文
```

`L1_standardized + C1_complete` 高分只能证明基础能力。真正有信息量的是 workflow 在 `L2/L3`、`C2/C3` 场景里还能不能稳定。

## 硬门槛

硬门槛在加权分计算完成后限制最终分数上限。

| Gate | 最高分 |
| --- | ---: |
| `task_not_solved` | 40 |
| `security_issue` | 50 |
| `public_api_break` | 55 |
| `required_tests_failed` | 60 |
| `unrelated_changes` | 65 |
| `hidden_tests_failed` | 70 |

## 什么算证据

每次运行都应该保留以下证据：

```text
task.md         本次 run 使用的 coding prompt 快照
transcript.md   AI/用户交互记录或摘要
events.jsonl    可选的 Claude Code 或 Codex hook 脱敏事件
diff.patch      最终代码变更
test.log        必跑测试和可选测试输出
run.json        评分前事实和 coding process evidence
score.json      review 分、hard gates 和最终分
```

`prepare_run.py` 创建这组证据骨架，把 coding task prompt 复制到 run 目录，并把目标仓库 clone 到隔离的 run worktree。`acceptance.md` 不会被复制，因为它是 reviewer-only 文件。`execute_run.py` 执行目标项目的 setup/test 命令，写入 `test.log`，写入 `diff.patch`，并更新 `run.json`。可选 hooks 会把过程事件追加到 `events.jsonl`；`summarize_run_events.py` 会从这些事件派生过程证据。人工 reviewer 通过 `score_run.py --set-review` 传入 `review.*` 分数，也可以用 `llm_review_run.py` 调用 OpenAI-compatible LLM 生成 review 维度。`score_run.py` 计算最终评分字段，并写入 `derived_hard_gates` 和最终合并后的 `hard_gates`。

当 `task.json` 定义 `scope.allowed_paths` 时，`execute_run.py` 会把已跟踪变更文件和 untracked 新文件一起与 allowlist 对比，并写入 `run.json.diff.scope_check=path_allowlist`、`unrelated_files_changed` 和 `unrelated_files`。如果没有 `scope`，无关文件状态是未知，而不是默认干净。

如果一次 run 需要额外的长文本评审说明，可以在 run 目录放自定义文件。它不属于标准协议；结构化 review 备注统一放在 `score.json.review_notes`。

v0.2 开始，`run.json` 也可以保留可选诊断证据：

```text
process_evidence  coding 过程中使用过的文档、工具、知识源和自检轨迹
adoption          可获得时记录 AI 生成行数、采纳行数和采纳率
context_metrics   用于知识库/SPEC/skills 分析的调用率、命中率、采纳率
```

## 最小有效比较

比较不同工作流时，必须使用同一批任务、同一模型预算、同一运行次数。

经验置信度：

```text
5 个任务      80% 适合调试 benchmark，30% 适合选择工作流
10-15 个任务  60% 适合淘汰弱工作流
30 个任务     75% 适合选择主力工作流
50+ 个任务    80-85% 适合优化工作流细节
```
