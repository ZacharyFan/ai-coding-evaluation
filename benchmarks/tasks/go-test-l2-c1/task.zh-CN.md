# 任务：补充结账跨领域集成测试

场景：结账链路（checkout）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C1_complete，C1：`docs/contexts/checkout.md` 完整说明 cart/pricing/inventory/shipping 的联动契约。

背景：

checkout 缺少同时覆盖 cart/pricing/inventory/shipping 的集成测试。

期望行为：

- 新增 TestBuildQuoteCombinesInventoryTaxAndShipping
- 断言库存、税费、运费共同影响结果
- 不要求改生产代码

复现命令：

```bash
./scripts/run_eval_case.sh go-test-l2-c1
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `checkout/**, cart/**, pricing/**, inventory/**, shipping/**, docs/contexts/checkout.md`。
