# Acceptance: Add fulfillment idempotency

Public acceptance:

- second call with same key does not repeat reserve/authorize/ship
- first success still writes outbox
- empty key errors

Hidden checks:

- Idempotency is implemented in the saga coordinator.
- The documented service protocol is preserved.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l3-c1
```
