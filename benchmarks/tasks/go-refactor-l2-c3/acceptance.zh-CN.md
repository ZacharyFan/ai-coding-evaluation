# 验收标准: 提取订阅激活决策

公开验收:

- 新增 activationDecision helper
- Activate 调用 helper
- 行为保持不变

隐藏检查:

- The helper coordinates multiple domain packages.
- No docs are added for C3.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c3
```
