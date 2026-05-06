# 验收标准: 新增结账折扣报价

公开验收:

- 百分比折扣应用在税费前
- 折后金额仍参与运费门槛
- 库存不足仍失败

隐藏检查:

- The feature crosses at least three domain packages.
- The documented checkout flow is preserved.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l2-c1
```
