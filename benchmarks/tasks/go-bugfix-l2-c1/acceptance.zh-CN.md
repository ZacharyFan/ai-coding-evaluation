# 验收标准: 结账校验所有库存行

公开验收:

- 任意订单行库存不足返回 error
- 税费和运费计算保持不变
- 联动 cart/pricing/inventory/shipping

隐藏检查:

- All line inventory is checked before returning a quote.
- The checkout context doc remains valid.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c1
```
