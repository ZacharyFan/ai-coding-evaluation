# 任务：新增退货预览

场景：退货链路（returns）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C2_partial，C2：`docs/contexts/returns.md` 只描述 happy path，失败路径和回滚语义不完整。

背景：

新增 returns.PreviewReturn，跨订单状态、退款金额、库存策略生成预览。

期望行为：

- 不可退订单返回原因
- 可退订单返回预计退款
- 不产生 ledger 或 inventory 副作用

复现命令：

```bash
./scripts/run_eval_case.sh go-feature-l2-c2
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `returns/**, orders/**, refunds/**, inventory/**, ledger/**, docs/contexts/returns.md`。
