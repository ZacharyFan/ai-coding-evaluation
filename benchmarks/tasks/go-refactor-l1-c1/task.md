# Task: Extract SKU normalization helper

Scenario: catalog (`catalog`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C1_complete, C1: `docs/contexts/catalog.md` fully documents fields, states, errors, and examples.

Context:

Catalog SKU cleanup should be centralized in an internal helper.

Expected behavior:

- adds normalizeSKU helper
- ValidateProduct and FindAvailableByTag reuse it
- public APIs stay unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `catalog/**, docs/contexts/catalog.md`.
