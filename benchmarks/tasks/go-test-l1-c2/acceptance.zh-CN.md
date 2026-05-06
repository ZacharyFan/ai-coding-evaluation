# 验收标准: 补充税率上限测试

公开验收:

- 新增 TestValidateRuleRejectsRateAboveCap
- 覆盖 2501 basis points
- 不修改生产行为

隐藏检查:

- A named test protects the cap.
- The test uses the taxrules package only.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l1-c2
```
