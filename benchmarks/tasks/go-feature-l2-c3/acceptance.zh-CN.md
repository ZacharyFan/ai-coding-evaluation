# 验收标准: 新增订阅换套餐预览

公开验收:

- 活跃 entitlement 才能预览
- 返回 prorated credit 和 next charge
- 冻结账户不可预览

隐藏检查:

- The feature crosses all subscription domains.
- Behavior is inferred without docs.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l2-c3
```
