# 验收标准: 补充订阅成功开通测试

公开验收:

- 新增 TestActivateCreatesInvoiceAndEntitlement
- 覆盖 invoice 创建和 entitlement 激活
- 不要求改生产代码

隐藏检查:

- The named test spans three domains.
- C3 remains undocumented.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l2-c3
```
