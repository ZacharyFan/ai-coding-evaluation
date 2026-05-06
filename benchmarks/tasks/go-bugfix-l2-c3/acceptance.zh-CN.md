# 验收标准: 冻结账户不可开通订阅

公开验收:

- Hold 账户返回 error
- 不创建 invoice
- 不激活 entitlement

隐藏检查:

- The fix coordinates account, billing, and entitlement.
- No C3 context doc is introduced.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c3
```
