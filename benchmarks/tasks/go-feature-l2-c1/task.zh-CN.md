# 任务：新增结账折扣报价

场景：结账链路（checkout）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C1_complete，C1：`docs/contexts/checkout.md` 完整说明 cart/pricing/inventory/shipping 的联动契约。

背景：

新增 checkout.BuildDiscountedQuote，将 cart 小计、pricing 折扣、tax、shipping 联动。

期望行为：

- 百分比折扣应用在税费前
- 折后金额仍参与运费门槛
- 库存不足仍失败

复现命令：

```bash
./scripts/run_eval_case.sh go-feature-l2-c1
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `checkout/**, cart/**, pricing/**, inventory/**, shipping/**, docs/contexts/checkout.md`。
