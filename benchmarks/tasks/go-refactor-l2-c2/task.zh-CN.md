# 任务：提取退货资格判断

场景：退货链路（returns）。

- 业务复杂度：L2_linked，多领域模型联动，必须理解 3 个以上领域包的协作。
- 上下文成熟度：C2_partial，C2：`docs/contexts/returns.md` 只描述 happy path，失败路径和回滚语义不完整。

背景：

returns.ProcessReturn 的资格判断需要提取为 helper。

期望行为：

- 新增 returnEligibilityReason
- ProcessReturn 和 PreviewReturn 复用
- 行为保持不变

复现命令：

```bash
./scripts/run_eval_case.sh go-refactor-l2-c2
```

约束：

- 不要为测试写特殊分支。
- 保持既有公开 API 兼容，除非本任务明确要求新增 API。
- diff 限制在 `returns/**, orders/**, refunds/**, inventory/**, ledger/**, docs/contexts/returns.md`。
