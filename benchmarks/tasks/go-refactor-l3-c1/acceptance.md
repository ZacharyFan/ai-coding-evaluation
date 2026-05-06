# Acceptance: Extract fulfillment compensation

Public acceptance:

- adds compensateAuthorization helper
- PlaceOrder uses it
- behavior stays unchanged

Hidden checks:

- The helper coordinates inventory and payment clients.
- Outbox publishing remains separate.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l3-c1
```
