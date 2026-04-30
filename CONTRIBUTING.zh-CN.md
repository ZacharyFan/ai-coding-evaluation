# 贡献评估用例

[英文版](CONTRIBUTING.md)

这个项目需要的是可复跑的工程任务，不是“听起来像真实需求”的提示词。

## 贡献路径

1. 复制最接近的任务类型模板：

   ```bash
   cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
   ```

2. 把 `task.json` 里的 `id` 改成新目录名。
3. 用真实代码仓库里的具体任务替换 `task.md`、`acceptance.md` 和 `tests.sh`。
4. 本地验证：

   ```bash
   python scripts/validate_task.py benchmarks/tasks/<task-id>
   pytest
   ```

## 任务目录契约

每个任务目录必须包含：

```text
task.json       机器可读元数据、预算、目标仓库、检查项和评分权重
task.md         展示给 workflow 的任务说明
acceptance.md   盲审用的人类可读验收标准
tests.sh        确定性的必跑检查，必须能用 ./tests.sh 执行
```

如果有助于 reviewer，欢迎补充 `task.zh-CN.md`、`acceptance.zh-CN.md` 等本地化文件。

`benchmarks/tasks/` 是真实 benchmark 集。模板保留在 `benchmarks/templates/`，默认不会被运行。

## 命名

使用稳定、可读的 id：

```text
bugfix-002
feature-003
refactor-002
test-002
frontend-002
integration-001
ci-001
```

`task.json` 里的 `id` 必须等于目录名。

## 必填元数据

按工作量设置 `effort_size`：

```text
small    局部、窄范围改动
medium   涉及少量文件，或需要明显调查
large    范围较宽，有预算压力
```

单独设置复杂度：

```text
business_complexity
  L1_standardized  直接 bugfix、简单 CRUD、配置、直接补测试
  L2_linked        字段联动、多步骤流程、集成任务、关联数据
  L3_complex       架构、深度定制 UI、复杂数据流或复杂推理

context_maturity
  C1_complete      文档、API、示例和项目知识足够
  C2_partial       上下文存在，但不完整、过时或分散
  C3_missing       agent 必须推断或补齐缺失上下文
```

`effort_size` 不是复杂度。任务可以小但复杂，也可以大但机械。

## 验收门槛

好用例应该具备：

- 固定的目标仓库和 `base_ref`
- 足够精确的复现步骤或入口点，让另一个人能重跑
- 必跑检查能在改动前失败，或能保护目标行为
- hidden checks 描述 reviewer 关注点，但不泄露解法
- 不依赖 agent 无法查看的私有上下文
- 不使用纯主观验收标准

## PR 检查清单

开 PR 前确认：

- `python scripts/validate_task.py benchmarks/tasks/<task-id>` 通过
- `pytest` 通过
- `tests.sh` 可执行
- 任务能从目标仓库的干净 checkout 重跑
- 评分权重仍然合计 100
- 贡献内容不包含私有代码、凭据、token、日志或客户数据
