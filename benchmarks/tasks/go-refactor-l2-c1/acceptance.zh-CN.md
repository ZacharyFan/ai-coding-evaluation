# 验收标准: 提取结账库存校验

公开验收:

- 新增 validateInventoryForLines
- BuildQuote 调用 helper
- 行为保持不变

隐藏检查:

- The helper coordinates cart lines and inventory snapshot.
- No domain package is merged into checkout.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c1
```
