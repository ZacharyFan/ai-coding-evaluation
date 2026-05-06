# Acceptance: Test catalog price boundaries

Public acceptance:

- adds TestValidateProductRejectsNegativePrice
- uses public catalog API only
- does not require production changes

Hidden checks:

- A named test covers negative price.
- The test runs under go test ./catalog.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l1-c1
```
