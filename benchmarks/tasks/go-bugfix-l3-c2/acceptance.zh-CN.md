# 验收标准: 支付结算失败不重复扣款

公开验收:

- 同一 invoice 第二次重试不重复 capture
- ledger 可在重试时补记
- 错误仍向上传递

隐藏检查:

- The fix handles cross-service idempotency.
- Partial docs are not expanded as the solution.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c2
```
