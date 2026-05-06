# 验收标准: 新增退货预览

公开验收:

- 不可退订单返回原因
- 可退订单返回预计退款
- 不产生 ledger 或 inventory 副作用

隐藏检查:

- The feature links orders and refunds without side effects.
- Partial docs are not expanded.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l2-c2
```
