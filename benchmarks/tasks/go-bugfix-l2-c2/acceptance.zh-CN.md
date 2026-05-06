# 验收标准: 退货失败不应回补库存

公开验收:

- ledger 失败时库存不变
- 成功退货仍记录 refund 和 ledger
- 联动 orders/refunds/inventory/ledger

隐藏检查:

- Failure ordering prevents partial local side effects.
- The partial docs are not treated as authoritative for failure paths.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c2
```
