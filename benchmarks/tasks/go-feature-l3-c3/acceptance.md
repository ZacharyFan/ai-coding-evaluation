# Acceptance: Add reconciliation discrepancy report

Public acceptance:

- report includes missing payouts
- report includes amount mismatches
- report is sorted by external ID

Hidden checks:

- The feature crosses payout, ledger, and notification concepts.
- No docs are added for C3.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l3-c3
```
