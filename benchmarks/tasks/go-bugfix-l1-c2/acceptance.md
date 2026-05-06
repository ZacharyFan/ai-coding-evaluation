# Acceptance: Round tax to the nearest cent

Public acceptance:

- half-cent and above rounds up
- exact-cent tax stays unchanged
- invalid rates still error

Hidden checks:

- Rounding is implemented in taxrules only.
- Partial docs are not edited as a shortcut.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c2
```
