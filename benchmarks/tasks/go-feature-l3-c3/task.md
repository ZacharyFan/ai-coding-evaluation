# Task: Add reconciliation discrepancy report

Scenario: settlement reconciliation (`settlement_reconciliation`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C3_missing, C3: no reconciliation context document exists; infer from service interfaces and tests.

Context:

Add settlement_reconciliation.BuildReport aggregating payout/ledger differences and notification status.

Expected behavior:

- report includes missing payouts
- report includes amount mismatches
- report is sorted by external ID

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l3-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `settlement_reconciliation/**`.
