# Acceptance: Test payment transient retry

Public acceptance:

- adds TestSettleInvoiceRetriesTransientGatewayError
- uses fake gateway and fake ledger
- does not require production changes

Hidden checks:

- The named test exercises a service-boundary retry.
- It runs under go test ./payment_saga.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l3-c2
```
