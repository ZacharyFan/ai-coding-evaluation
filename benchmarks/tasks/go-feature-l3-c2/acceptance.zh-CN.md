# 验收标准: 新增支付退款 Saga

公开验收:

- 先调用 gateway refund
- 再记录 ledger refund
- ledger 失败返回 error 并保留退款 ID

隐藏检查:

- The feature crosses service interfaces.
- Retry semantics remain compatible with partial docs.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l3-c2
```
