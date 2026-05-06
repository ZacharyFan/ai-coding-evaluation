# 验收标准: 新增对账差异报告

公开验收:

- 报告包含 missing payout
- 报告包含 amount mismatch
- 报告按 external ID 排序

隐藏检查:

- The feature crosses payout, ledger, and notification concepts.
- No docs are added for C3.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l3-c3
```
