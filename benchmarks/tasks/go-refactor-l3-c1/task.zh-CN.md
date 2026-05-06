# 任务：提取履约补偿流程

场景：履约 Saga（fulfillment_saga）。

- 业务复杂度：L3_complex，分布式事务/跨服务调用，包含接口边界、补偿、幂等或 outbox。
- 上下文成熟度：C1_complete，C1：`docs/contexts/fulfillment_saga.md` 完整说明跨服务协议、幂等、补偿和 outbox。

背景：

fulfillment_saga 的跨服务补偿逻辑需要抽成 helper。

期望行为：

- 新增 compensateAuthorization helper
- PlaceOrder 使用 helper
- 行为保持不变

复现命令：

```bash
./scripts/run_eval_case.sh go-refactor-l3-c1
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `fulfillment_saga/**, docs/contexts/fulfillment_saga.md`。
