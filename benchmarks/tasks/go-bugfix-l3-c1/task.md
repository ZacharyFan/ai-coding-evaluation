# Task: Compensate fulfillment carrier failure

Scenario: fulfillment saga (`fulfillment_saga`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C1_complete, C1: `docs/contexts/fulfillment_saga.md` fully documents service protocols, idempotency, compensation, and outbox.

Context:

fulfillment_saga.Coordinator does not release inventory or void payment when carrier creation fails.

Expected behavior:

- carrier failure releases inventory
- carrier failure voids payment authorization
- fulfilled outbox event is not published

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `fulfillment_saga/**, docs/contexts/fulfillment_saga.md`.
