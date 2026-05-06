# 任务：新增资料显示名

场景：客户资料（customerprofile）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C3_missing，C3：没有对应业务文档，只能从代码、命名和普通测试推断。

背景：

新增 customerprofile.DisplayName，根据姓名字段生成展示名。

期望行为：

- 优先使用 FirstName + LastName
- 缺失姓名时回退 Email
- 空资料返回 anonymous

复现命令：

```bash
./scripts/run_eval_case.sh go-feature-l1-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `customerprofile/**`。
