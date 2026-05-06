# 验收标准: 补充结账跨领域集成测试

公开验收:

- 新增 TestBuildQuoteCombinesInventoryTaxAndShipping
- 断言库存、税费、运费共同影响结果
- 不要求改生产代码

隐藏检查:

- The named test crosses the documented domains.
- It runs under go test ./checkout.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l2-c1
```
