# Acceptance: Test reconciliation notification failure

Public acceptance:

- adds TestReconcileReturnsNotificationFailure
- uses fake payout/ledger/notification clients
- does not require production changes

Hidden checks:

- The named test exercises three service clients.
- C3 remains undocumented.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l3-c3
```
