# Task: Extract checkout inventory validation

Scenario: checkout flow (`checkout`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C1_complete, C1: `docs/contexts/checkout.md` fully documents the cart/pricing/inventory/shipping contract.

Context:

checkout.BuildQuote inventory validation should be extracted.

Expected behavior:

- adds validateInventoryForLines
- BuildQuote calls it
- behavior stays unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `checkout/**, cart/**, pricing/**, inventory/**, shipping/**, docs/contexts/checkout.md`.
