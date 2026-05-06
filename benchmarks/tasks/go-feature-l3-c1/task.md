# Task: Add fulfillment idempotency

Scenario: fulfillment saga (`fulfillment_saga`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C1_complete, C1: `docs/contexts/fulfillment_saga.md` fully documents service protocols, idempotency, compensation, and outbox.

Context:

fulfillment_saga.PlaceOrder should use IdempotencyKey to avoid duplicate service calls.

Expected behavior:

- second call with same key does not repeat reserve/authorize/ship
- first success still writes outbox
- empty key errors

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l3-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `fulfillment_saga/**, docs/contexts/fulfillment_saga.md`.
