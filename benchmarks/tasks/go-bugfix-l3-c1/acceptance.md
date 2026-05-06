# Acceptance: Compensate fulfillment carrier failure

Public acceptance:

- carrier failure releases inventory
- carrier failure voids payment authorization
- fulfilled outbox event is not published

Hidden checks:

- The fix follows documented compensation order.
- Service interfaces remain unchanged.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c1
```
