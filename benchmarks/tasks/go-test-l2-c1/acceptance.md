# Acceptance: Test checkout cross-domain quote

Public acceptance:

- adds TestBuildQuoteCombinesInventoryTaxAndShipping
- asserts inventory/tax/shipping jointly affect output
- does not require production changes

Hidden checks:

- The named test crosses the documented domains.
- It runs under go test ./checkout.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l2-c1
```
