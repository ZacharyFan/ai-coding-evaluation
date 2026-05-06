# Acceptance: Extract checkout inventory validation

Public acceptance:

- adds validateInventoryForLines
- BuildQuote calls it
- behavior stays unchanged

Hidden checks:

- The helper coordinates cart lines and inventory snapshot.
- No domain package is merged into checkout.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c1
```
