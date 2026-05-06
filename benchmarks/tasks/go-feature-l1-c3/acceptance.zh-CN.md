# 验收标准: 新增资料显示名

公开验收:

- 优先使用 FirstName + LastName
- 缺失姓名时回退 Email
- 空资料返回 anonymous

隐藏检查:

- No context doc is created.
- The feature remains a single aggregate method.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l1-c3
```
