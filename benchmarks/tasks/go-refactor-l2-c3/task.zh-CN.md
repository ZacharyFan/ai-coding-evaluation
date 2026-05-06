# 任务：提取订阅激活决策

场景：订阅开通（subscriptions）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C3_missing，C3：没有订阅开通上下文文档，必须从 account/billing/entitlement 代码推断。

背景：

subscriptions.Activate 的 account/billing/entitlement 判断需要提取。

期望行为：

- 新增 activationDecision helper
- Activate 调用 helper
- 行为保持不变

复现命令：

```bash
./scripts/run_eval_case.sh go-refactor-l2-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `subscriptions/**, account/**, billing/**, entitlement/**`。
