# Acceptance: Add return preview

Public acceptance:

- ineligible orders return a reason
- eligible orders return expected refund
- no ledger or inventory side effects

Hidden checks:

- The feature links orders and refunds without side effects.
- Partial docs are not expanded.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l2-c2
```
