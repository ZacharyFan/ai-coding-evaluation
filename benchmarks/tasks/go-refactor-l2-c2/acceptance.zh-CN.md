# 验收标准: 提取退货资格判断

公开验收:

- 新增 returnEligibilityReason
- ProcessReturn 和 PreviewReturn 复用
- 行为保持不变

隐藏检查:

- Eligibility spans order state and refund policy.
- No external API is removed.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c2
```
