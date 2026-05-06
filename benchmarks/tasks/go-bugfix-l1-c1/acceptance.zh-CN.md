# 验收标准: 校验商品 SKU 必填

公开验收:

- 空白 SKU 返回 error
- 合法 active 商品继续通过
- 错误来自 catalog 单领域模型

隐藏检查:

- Blank SKU validation follows the catalog context doc.
- No cross-domain package is introduced.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c1
```
