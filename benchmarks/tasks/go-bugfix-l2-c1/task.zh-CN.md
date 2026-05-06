# 任务：结账校验所有库存行

场景：结账链路（checkout）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C1_complete，C1：`docs/contexts/checkout.md` 完整说明 cart/pricing/inventory/shipping 的联动契约。

背景：

checkout.BuildQuote 只校验第一条库存行，跨 cart/pricing/inventory/shipping 的完整文档说明应校验全部行。

期望行为：

- 任意订单行库存不足返回 error
- 税费和运费计算保持不变
- 联动 cart/pricing/inventory/shipping

复现命令：

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c1
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `checkout/**, cart/**, pricing/**, inventory/**, shipping/**, docs/contexts/checkout.md`。
