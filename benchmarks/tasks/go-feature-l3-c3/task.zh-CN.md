# 任务：新增对账差异报告

场景：结算对账（settlement_reconciliation）。

- 业务复杂度：L3_complex，分布式事务/跨服务调用，包含接口边界、补偿、幂等或 outbox。
- 上下文成熟度：C3_missing，C3：没有结算对账上下文文档，只能从跨服务接口和测试推断。

背景：

新增 settlement_reconciliation.BuildReport，聚合 payout/ledger 差异和通知状态。

期望行为：

- 报告包含 missing payout
- 报告包含 amount mismatch
- 报告按 external ID 排序

复现命令：

```bash
./scripts/run_eval_case.sh go-feature-l3-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `settlement_reconciliation/**`。
