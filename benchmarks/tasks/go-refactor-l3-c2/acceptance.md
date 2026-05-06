# Acceptance: Extract payment retry policy

Public acceptance:

- adds shouldRetryPaymentError
- SettleInvoice uses it
- behavior stays unchanged

Hidden checks:

- Retry policy is centralized.
- Gateway and ledger interfaces remain unchanged.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c2
```
