# Task: Reject blank catalog SKUs

Scenario: catalog (`catalog`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C1_complete, C1: `docs/contexts/catalog.md` fully documents fields, states, errors, and examples.

Context:

catalog.ValidateProduct does not reject blank SKUs.

Expected behavior:

- blank SKUs return an error
- valid active products still pass
- the fix stays inside the catalog domain

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `catalog/**, docs/contexts/catalog.md`.
