# 验收标准: 补充履约 outbox 测试

公开验收:

- 新增 TestPlaceOrderPublishesOutboxEvent
- 使用 fake service clients
- 不要求改生产代码

隐藏检查:

- The named test exercises service boundaries.
- It runs under go test ./fulfillment_saga.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l3-c1
```
