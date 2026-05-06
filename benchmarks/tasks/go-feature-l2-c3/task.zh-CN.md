# 任务：新增订阅换套餐预览

场景：订阅开通（subscriptions）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C3_missing，C3：没有订阅开通上下文文档，必须从 account/billing/entitlement 代码推断。

背景：

新增 subscriptions.PreviewPlanChange，联动 account/billing/entitlement 计算换套餐影响。

期望行为：

- 活跃 entitlement 才能预览
- 返回 prorated credit 和 next charge
- 冻结账户不可预览

复现命令：

```bash
./scripts/run_eval_case.sh go-feature-l2-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `subscriptions/**, account/**, billing/**, entitlement/**`。
