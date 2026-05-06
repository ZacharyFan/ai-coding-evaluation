# Acceptance: Extract reconciliation matching engine

Public acceptance:

- adds matchPayoutsToLedger helper
- Reconcile and BuildReport reuse it
- behavior stays unchanged

Hidden checks:

- Matching is isolated from notification side effects.
- No context docs are introduced.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c3
```
