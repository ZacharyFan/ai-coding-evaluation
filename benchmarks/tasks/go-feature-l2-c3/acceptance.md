# Acceptance: Add subscription plan-change preview

Public acceptance:

- requires active entitlement
- returns prorated credit and next charge
- held accounts cannot preview

Hidden checks:

- The feature crosses all subscription domains.
- Behavior is inferred without docs.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l2-c3
```
