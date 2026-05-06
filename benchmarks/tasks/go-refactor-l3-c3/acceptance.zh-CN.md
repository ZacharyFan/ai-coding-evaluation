# 验收标准: 提取对账匹配引擎

公开验收:

- 新增 matchPayoutsToLedger helper
- Reconcile 和 BuildReport 复用
- 行为保持不变

隐藏检查:

- Matching is isolated from notification side effects.
- No context docs are introduced.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c3
```
