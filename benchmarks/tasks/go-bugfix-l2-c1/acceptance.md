# Acceptance: Validate all checkout inventory lines

Public acceptance:

- any unavailable line returns an error
- tax and shipping math stay unchanged
- links cart/pricing/inventory/shipping

Hidden checks:

- All line inventory is checked before returning a quote.
- The checkout context doc remains valid.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c1
```
