# 验收标准: 新增按标签筛选可售商品

公开验收:

- 只返回 active 且包含标签的商品
- 结果按 SKU 排序
- 输入切片不被修改

隐藏检查:

- The feature uses only catalog.Product.
- The behavior follows documented tag examples.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l1-c1
```
