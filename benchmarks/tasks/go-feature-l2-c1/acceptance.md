# Acceptance: Add discounted checkout quotes

Public acceptance:

- percent discount applies before tax
- discounted amount participates in shipping threshold
- inventory failures still fail

Hidden checks:

- The feature crosses at least three domain packages.
- The documented checkout flow is preserved.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l2-c1
```
