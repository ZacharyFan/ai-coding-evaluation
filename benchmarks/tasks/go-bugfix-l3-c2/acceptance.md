# Acceptance: Avoid duplicate capture after ledger failure

Public acceptance:

- retry for same invoice does not capture again
- ledger can be recorded on retry
- errors still propagate

Hidden checks:

- The fix handles cross-service idempotency.
- Partial docs are not expanded as the solution.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c2
```
