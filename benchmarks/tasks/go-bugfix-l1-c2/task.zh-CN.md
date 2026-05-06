# 任务：税费按分四舍五入

场景：税务规则（taxrules）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C2_partial，C2：`docs/contexts/taxrules.md` 只有部分税率说明，舍入和上限边界缺失。

背景：

taxrules.TaxCents 对半分以上税额向下截断；部分文档没有写舍入边界。

期望行为：

- 半分及以上进位
- 整数分税额保持不变
- 仍拒绝非法税率

复现命令：

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c2
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `taxrules/**, docs/contexts/taxrules.md`。
