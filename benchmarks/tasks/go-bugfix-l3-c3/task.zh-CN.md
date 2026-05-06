# 任务：对账通知保持幂等

场景：结算对账（settlement_reconciliation）。

- 业务复杂度：L3_complex，分布式事务/跨服务调用，包含接口边界、补偿、幂等或 outbox。
- 上下文成熟度：C3_missing，C3：没有结算对账上下文文档，只能从跨服务接口和测试推断。

背景：

settlement_reconciliation.Reconcile 重跑同一 batch 会重复发送通知。

期望行为：

- 同一 batch discrepancy 只通知一次
- 不同 batch 仍可通知
- 不改变 payout/ledger 匹配结果

复现命令：

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `settlement_reconciliation/**`。
