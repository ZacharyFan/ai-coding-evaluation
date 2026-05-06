# 验收标准: 补充成功退货联动测试

公开验收:

- 新增 TestProcessReturnRecordsLedgerAndRestocksOnSuccess
- 覆盖 refund 金额、库存回补和 ledger 记录
- 不要求改生产代码

隐藏检查:

- The named test captures the documented happy path.
- It runs under go test ./returns.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l2-c2
```
