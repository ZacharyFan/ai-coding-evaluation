# 验收标准: 提取资料校验 helper

公开验收:

- 新增 validateProfileIdentity helper
- Validate 调用 helper
- 行为保持不变

隐藏检查:

- The helper is package-local.
- No customerprofile docs are added.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c3
```
