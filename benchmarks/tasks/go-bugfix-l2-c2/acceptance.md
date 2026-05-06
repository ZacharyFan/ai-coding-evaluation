# Acceptance: Avoid restock on failed return ledger

Public acceptance:

- inventory is unchanged when ledger fails
- successful returns still record refund and ledger
- links orders/refunds/inventory/ledger

Hidden checks:

- Failure ordering prevents partial local side effects.
- The partial docs are not treated as authoritative for failure paths.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c2
```
