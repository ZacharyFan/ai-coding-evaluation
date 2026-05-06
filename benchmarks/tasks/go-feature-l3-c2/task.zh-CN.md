# 任务：新增支付退款 Saga

场景：支付 Saga（payment_saga）。

- 业务复杂度：L3_complex，分布式事务/跨服务调用，包含接口边界、补偿、幂等或 outbox。
- 上下文成熟度：C2_partial，C2：`docs/contexts/payment_saga.md` 只有部分接口文档，重试和幂等说明缺失。

背景：

新增 payment_saga.RefundInvoice，跨 PaymentGateway 和 LedgerClient 完成退款。

期望行为：

- 先调用 gateway refund
- 再记录 ledger refund
- ledger 失败返回 error 并保留退款 ID

复现命令：

```bash
./scripts/run_eval_case.sh go-feature-l3-c2
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `payment_saga/**, docs/contexts/payment_saga.md`。
