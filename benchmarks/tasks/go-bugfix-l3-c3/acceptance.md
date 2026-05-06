# Acceptance: Make reconciliation notifications idempotent

Public acceptance:

- same-batch discrepancies notify once
- different batches can still notify
- matching results stay unchanged

Hidden checks:

- The fix uses service-boundary idempotency.
- No C3 context doc is created.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c3
```
