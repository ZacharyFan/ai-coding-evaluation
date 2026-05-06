# Acceptance: Add customer display names

Public acceptance:

- uses FirstName + LastName first
- falls back to Email when names are missing
- empty profile returns anonymous

Hidden checks:

- No context doc is created.
- The feature remains a single aggregate method.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l1-c3
```
