# 验收标准: 对账通知保持幂等

公开验收:

- 同一 batch discrepancy 只通知一次
- 不同 batch 仍可通知
- 不改变 payout/ledger 匹配结果

隐藏检查:

- The fix uses service-boundary idempotency.
- No C3 context doc is created.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c3
```
