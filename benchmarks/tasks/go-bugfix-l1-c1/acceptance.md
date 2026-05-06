# Acceptance: Reject blank catalog SKUs

Public acceptance:

- blank SKUs return an error
- valid active products still pass
- the fix stays inside the catalog domain

Hidden checks:

- Blank SKU validation follows the catalog context doc.
- No cross-domain package is introduced.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c1
```
