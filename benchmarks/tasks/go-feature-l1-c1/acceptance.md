# Acceptance: Add available-product tag filtering

Public acceptance:

- returns only active products with the tag
- sorts results by SKU
- does not mutate input

Hidden checks:

- The feature uses only catalog.Product.
- The behavior follows documented tag examples.

Required command:

```bash
./scripts/run_eval_case.sh go-feature-l1-c1
```
