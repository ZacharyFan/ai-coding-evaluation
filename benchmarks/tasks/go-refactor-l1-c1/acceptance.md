# Acceptance: Extract SKU normalization helper

Public acceptance:

- adds normalizeSKU helper
- ValidateProduct and FindAvailableByTag reuse it
- public APIs stay unchanged

Hidden checks:

- SKU normalization is centralized.
- No exported field or type is renamed.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c1
```
