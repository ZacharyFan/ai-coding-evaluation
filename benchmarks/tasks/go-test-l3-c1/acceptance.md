# Acceptance: Test fulfillment outbox event

Public acceptance:

- adds TestPlaceOrderPublishesOutboxEvent
- uses fake service clients
- does not require production changes

Hidden checks:

- The named test exercises service boundaries.
- It runs under go test ./fulfillment_saga.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l3-c1
```
