# 验收标准: 命名 basis points 分母

公开验收:

- 新增 BasisPointsDenominator
- 税费计算使用常量
- 行为保持不变

隐藏检查:

- No raw denominator remains in production tax code.
- Public tax functions stay compatible.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c2
```
