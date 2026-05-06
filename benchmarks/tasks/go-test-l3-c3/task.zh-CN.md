# 任务：补充对账通知失败测试

场景：结算对账（settlement_reconciliation）。

- 业务复杂度：L3_complex，分布式事务/跨服务调用，包含接口边界、补偿、幂等或 outbox。
- 上下文成熟度：C3_missing，C3：没有结算对账上下文文档，只能从跨服务接口和测试推断。

背景：

settlement_reconciliation 缺少 NotificationClient 失败时返回 error 的测试。

期望行为：

- 新增 TestReconcileReturnsNotificationFailure
- 使用 fake payout/ledger/notification clients
- 不要求改生产代码

复现命令：

```bash
./scripts/run_eval_case.sh go-test-l3-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `settlement_reconciliation/**`。
