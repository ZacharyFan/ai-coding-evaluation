# 验收标准: 提取支付重试策略

公开验收:

- 新增 shouldRetryPaymentError
- SettleInvoice 使用 helper
- 行为保持不变

隐藏检查:

- Retry policy is centralized.
- Gateway and ledger interfaces remain unchanged.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c2
```
