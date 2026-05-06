# Acceptance: Name the basis-points denominator

Public acceptance:

- adds BasisPointsDenominator
- tax code uses the constant
- behavior stays unchanged

Hidden checks:

- No raw denominator remains in production tax code.
- Public tax functions stay compatible.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c2
```
