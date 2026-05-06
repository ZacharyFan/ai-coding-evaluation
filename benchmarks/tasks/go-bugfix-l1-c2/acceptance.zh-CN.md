# 验收标准: 税费按分四舍五入

公开验收:

- 半分及以上进位
- 整数分税额保持不变
- 仍拒绝非法税率

隐藏检查:

- Rounding is implemented in taxrules only.
- Partial docs are not edited as a shortcut.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c2
```
