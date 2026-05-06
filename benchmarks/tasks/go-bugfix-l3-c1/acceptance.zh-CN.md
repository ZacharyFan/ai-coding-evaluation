# 验收标准: 履约承运失败执行补偿

公开验收:

- carrier 失败时释放库存
- carrier 失败时撤销 payment authorization
- 不写入已履约 outbox

隐藏检查:

- The fix follows documented compensation order.
- Service interfaces remain unchanged.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c1
```
