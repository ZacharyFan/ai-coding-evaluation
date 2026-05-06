# Task: Avoid duplicate capture after ledger failure

Scenario: payment saga (`payment_saga`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C2_partial, C2: `docs/contexts/payment_saga.md` has partial interface docs and omits retry/idempotency rules.

Context:

payment_saga.SettleInvoice captures again after a ledger failure retry; partial docs omit idempotency.

Expected behavior:

- retry for same invoice does not capture again
- ledger can be recorded on retry
- errors still propagate

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `payment_saga/**, docs/contexts/payment_saga.md`.
