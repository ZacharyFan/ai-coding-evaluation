# 任务：冻结账户不可开通订阅

场景：订阅开通（subscriptions）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C3_missing，C3：没有订阅开通上下文文档，必须从 account/billing/entitlement 代码推断。

背景：

subscriptions.Activate 忽略 account.Hold，仍会 billing 并开 entitlement。

期望行为：

- Hold 账户返回 error
- 不创建 invoice
- 不激活 entitlement

复现命令：

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `subscriptions/**, account/**, billing/**, entitlement/**`。
