# 任务：补充删除资料不可营销测试

场景：客户资料（customerprofile）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C3_missing，C3：没有对应业务文档，只能从代码、命名和普通测试推断。

背景：

customerprofile.CanSendMarketing 缺少 Deleted=true 的测试。

期望行为：

- 新增 TestCanSendMarketingRejectsDeletedProfiles
- 覆盖 opt-in 但 deleted 的资料
- 不要求改生产代码

复现命令：

```bash
./scripts/run_eval_case.sh go-test-l1-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `customerprofile/**`。
