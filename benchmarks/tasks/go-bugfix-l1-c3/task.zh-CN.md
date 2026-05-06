# 任务：邮箱规范化转小写

场景：客户资料（customerprofile）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C3_missing，C3：没有对应业务文档，只能从代码、命名和普通测试推断。

背景：

customerprofile.NormalizeEmail 只 trim，没有转小写；没有文档可查。

期望行为：

- 本地名和域名转小写
- 无 @ 仍返回 error
- 只修改 customerprofile

复现命令：

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c3
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `customerprofile/**`。
