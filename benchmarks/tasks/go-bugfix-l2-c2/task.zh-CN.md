# 任务：退货失败不应回补库存

场景：退货链路（returns）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C2_partial，C2：`docs/contexts/returns.md` 只描述 happy path，失败路径和回滚语义不完整。

背景：

returns.ProcessReturn 在 ledger 失败时已经回补 inventory；partial 文档没有说明失败路径。

期望行为：

- ledger 失败时库存不变
- 成功退货仍记录 refund 和 ledger
- 联动 orders/refunds/inventory/ledger

复现命令：

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c2
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `returns/**, orders/**, refunds/**, inventory/**, ledger/**, docs/contexts/returns.md`。
