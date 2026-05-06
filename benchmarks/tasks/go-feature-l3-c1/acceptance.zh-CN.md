# 验收标准: 新增履约幂等键

公开验收:

- 同一 key 第二次调用不重复 reserve/authorize/ship
- 首次成功仍写 outbox
- 空 key 返回 error

隐藏检查:

- Idempotency is implemented in the saga coordinator.
- The documented service protocol is preserved.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l3-c1
```
