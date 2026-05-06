# 验收标准: 邮箱规范化转小写

公开验收:

- 本地名和域名转小写
- 无 @ 仍返回 error
- 只修改 customerprofile

隐藏检查:

- The behavior is inferred from code/tests, not docs.
- No new context doc is added for C3.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c3
```
