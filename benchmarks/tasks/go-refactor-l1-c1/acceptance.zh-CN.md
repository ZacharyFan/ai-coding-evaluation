# 验收标准: 提取 SKU 规范化 helper

公开验收:

- 新增 normalizeSKU helper
- ValidateProduct 和 FindAvailableByTag 复用 helper
- 公开 API 保持不变

隐藏检查:

- SKU normalization is centralized.
- No exported field or type is renamed.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c1
```
