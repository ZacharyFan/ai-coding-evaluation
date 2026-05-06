# 验收标准: 新增免税分类判断

公开验收:

- food 和 medicine 免税
- 大小写不敏感
- 未知分类不免税

隐藏检查:

- The feature is single-domain tax logic.
- No checkout or order package is touched.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l1-c2
```
