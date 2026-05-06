# 验收标准: 提取履约补偿流程

公开验收:

- 新增 compensateAuthorization helper
- PlaceOrder 使用 helper
- 行为保持不变

隐藏检查:

- The helper coordinates inventory and payment clients.
- Outbox publishing remains separate.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c1
```
