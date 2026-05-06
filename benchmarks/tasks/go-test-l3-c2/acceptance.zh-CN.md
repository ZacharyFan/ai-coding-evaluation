# 验收标准: 补充支付 transient 重试测试

公开验收:

- 新增 TestSettleInvoiceRetriesTransientGatewayError
- 使用 fake gateway 和 fake ledger
- 不要求改生产代码

隐藏检查:

- The named test exercises a service-boundary retry.
- It runs under go test ./payment_saga.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l3-c2
```
