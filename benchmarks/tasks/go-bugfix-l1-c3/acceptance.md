# Acceptance: Lowercase normalized emails

Public acceptance:

- local and domain parts are lowercased
- missing @ still errors
- changes stay in customerprofile

Hidden checks:

- The behavior is inferred from code/tests, not docs.
- No new context doc is added for C3.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c3
```
