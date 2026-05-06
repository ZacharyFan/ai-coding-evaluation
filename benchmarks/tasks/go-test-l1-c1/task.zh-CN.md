# 任务：补充商品价格边界测试

场景：商品目录（catalog）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C1_complete，C1：`docs/contexts/catalog.md` 完整说明字段约束、状态、错误语义和示例。

背景：

catalog.ValidateProduct 缺少负价格边界测试。

期望行为：

- 新增 TestValidateProductRejectsNegativePrice
- 测试只使用 catalog 包公开 API
- 不要求修改生产代码

复现命令：

```bash
./scripts/run_eval_case.sh go-test-l1-c1
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `catalog/**, docs/contexts/catalog.md`。
