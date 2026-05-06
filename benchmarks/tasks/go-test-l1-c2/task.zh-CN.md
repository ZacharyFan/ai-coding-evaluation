# 任务：补充税率上限测试

场景：税务规则（taxrules）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C2_partial，C2：`docs/contexts/taxrules.md` 只有部分税率说明，舍入和上限边界缺失。

背景：

taxrules.ValidateRule 缺少超过税率上限的测试。

期望行为：

- 新增 TestValidateRuleRejectsRateAboveCap
- 覆盖 2501 basis points
- 不修改生产行为

复现命令：

```bash
./scripts/run_eval_case.sh go-test-l1-c2
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `taxrules/**, docs/contexts/taxrules.md`。
