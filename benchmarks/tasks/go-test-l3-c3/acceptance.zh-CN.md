# 验收标准: 补充对账通知失败测试

公开验收:

- 新增 TestReconcileReturnsNotificationFailure
- 使用 fake payout/ledger/notification clients
- 不要求改生产代码

隐藏检查:

- The named test exercises three service clients.
- C3 remains undocumented.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l3-c3
```
