# Task: Add payment refund saga

Scenario: payment saga (`payment_saga`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C2_partial, C2: `docs/contexts/payment_saga.md` has partial interface docs and omits retry/idempotency rules.

Context:

Add payment_saga.RefundInvoice across PaymentGateway and LedgerClient.

Expected behavior:

- calls gateway refund first
- records ledger refund second
- ledger failure returns error with refund ID retained

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l3-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `payment_saga/**, docs/contexts/payment_saga.md`.
