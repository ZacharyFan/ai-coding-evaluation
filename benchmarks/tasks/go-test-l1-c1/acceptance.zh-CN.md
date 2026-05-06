# 验收标准: 补充商品价格边界测试

公开验收:

- 新增 TestValidateProductRejectsNegativePrice
- 测试只使用 catalog 包公开 API
- 不要求修改生产代码

隐藏检查:

- A named test covers negative price.
- The test runs under go test ./catalog.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l1-c1
```
