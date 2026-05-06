# Acceptance: Add exempt category handling

Public acceptance:

- food and medicine are exempt
- matching is case-insensitive
- unknown categories are taxable

Hidden checks:

- The feature is single-domain tax logic.
- No checkout or order package is touched.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l1-c2
```
