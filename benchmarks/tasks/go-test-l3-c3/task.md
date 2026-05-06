# Task: Test reconciliation notification failure

Scenario: settlement reconciliation (`settlement_reconciliation`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C3_missing, C3: no reconciliation context document exists; infer from service interfaces and tests.

Context:

settlement_reconciliation lacks coverage for NotificationClient failures.

Expected behavior:

- adds TestReconcileReturnsNotificationFailure
- uses fake payout/ledger/notification clients
- does not require production changes

Reproduction:

```bash
./scripts/run_eval_case.sh go-test-l3-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `settlement_reconciliation/**`.
