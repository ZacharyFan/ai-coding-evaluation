# 任务：提取 SKU 规范化 helper

场景：商品目录（catalog）。

- 业务复杂度：L1_standardized，单领域模型，只涉及一个包/聚合。
- 上下文成熟度：C1_complete，C1：`docs/contexts/catalog.md` 完整说明字段约束、状态、错误语义和示例。

背景：

catalog 的 SKU 清理逻辑需要集中到内部 helper。

期望行为：

- 新增 normalizeSKU helper
- ValidateProduct 和 FindAvailableByTag 复用 helper
- 公开 API 保持不变

复现命令：

```bash
./scripts/run_eval_case.sh go-refactor-l1-c1
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `catalog/**, docs/contexts/catalog.md`。
