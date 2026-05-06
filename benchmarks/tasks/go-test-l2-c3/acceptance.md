# Acceptance: Test successful subscription activation

Public acceptance:

- adds TestActivateCreatesInvoiceAndEntitlement
- covers invoice creation and entitlement activation
- does not require production changes

Hidden checks:

- The named test spans three domains.
- C3 remains undocumented.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l2-c3
```
