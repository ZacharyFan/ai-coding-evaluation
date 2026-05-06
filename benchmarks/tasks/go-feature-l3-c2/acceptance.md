# Acceptance: Add payment refund saga

Public acceptance:

- calls gateway refund first
- records ledger refund second
- ledger failure returns error with refund ID retained

Hidden checks:

- The feature crosses service interfaces.
- Retry semantics remain compatible with partial docs.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l3-c2
```
