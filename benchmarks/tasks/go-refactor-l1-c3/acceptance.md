# Acceptance: Extract profile validation helper

Public acceptance:

- adds validateProfileIdentity helper
- Validate calls the helper
- behavior stays unchanged

Hidden checks:

- The helper is package-local.
- No customerprofile docs are added.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c3
```
