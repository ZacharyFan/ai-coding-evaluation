# Acceptance: Extract subscription activation decision

Public acceptance:

- adds activationDecision helper
- Activate calls it
- behavior stays unchanged

Hidden checks:

- The helper coordinates multiple domain packages.
- No docs are added for C3.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c3
```
