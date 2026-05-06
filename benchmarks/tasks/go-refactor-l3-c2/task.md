# Task: Extract payment retry policy

Scenario: payment saga (`payment_saga`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C2_partial, C2: `docs/contexts/payment_saga.md` has partial interface docs and omits retry/idempotency rules.

Context:

payment_saga transient retry logic should be extracted.

Expected behavior:

- adds shouldRetryPaymentError
- SettleInvoice uses it
- behavior stays unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `payment_saga/**, docs/contexts/payment_saga.md`.
