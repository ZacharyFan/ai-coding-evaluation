# 任务：提取资料校验 helper

场景：客户资料（customerprofile）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C3_missing，C3：没有对应业务文档，只能从代码、命名和普通测试推断。

背景：

customerprofile.Validate 的字段校验需要拆成内部 helper。

期望行为：

- 新增 validateProfileIdentity helper
- Validate 调用 helper
- 行为保持不变

复现命令：

```bash
./scripts/run_eval_case.sh go-refactor-l1-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `customerprofile/**`。
