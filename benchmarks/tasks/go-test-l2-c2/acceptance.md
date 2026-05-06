# Acceptance: Test successful return side effects

Public acceptance:

- adds TestProcessReturnRecordsLedgerAndRestocksOnSuccess
- covers refund amount, inventory restock, and ledger entry
- does not require production changes

Hidden checks:

- The named test captures the documented happy path.
- It runs under go test ./returns.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l2-c2
```
