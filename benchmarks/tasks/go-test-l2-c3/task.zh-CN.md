# 任务：补充订阅成功开通测试

场景：订阅开通（subscriptions）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C3_missing，C3：没有订阅开通上下文文档，必须从 account/billing/entitlement 代码推断。

背景：

subscriptions 缺少成功路径同时覆盖 account/billing/entitlement 的测试。

期望行为：

- 新增 TestActivateCreatesInvoiceAndEntitlement
- 覆盖 invoice 创建和 entitlement 激活
- 不要求改生产代码

复现命令：

```bash
./scripts/run_eval_case.sh go-test-l2-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `subscriptions/**, account/**, billing/**, entitlement/**`。
