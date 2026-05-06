# Task: Add available-product tag filtering

Scenario: catalog (`catalog`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C1_complete, C1: `docs/contexts/catalog.md` fully documents fields, states, errors, and examples.

Context:

Add catalog.FindAvailableByTag within the catalog domain.

Expected behavior:

- returns only active products with the tag
- sorts results by SKU
- does not mutate input

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l1-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `catalog/**, docs/contexts/catalog.md`.
