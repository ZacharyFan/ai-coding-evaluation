# Task: Add discounted checkout quotes

Scenario: checkout flow (`checkout`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C1_complete, C1: `docs/contexts/checkout.md` fully documents the cart/pricing/inventory/shipping contract.

Context:

Add checkout.BuildDiscountedQuote linking cart subtotal, pricing discount, tax, and shipping.

Expected behavior:

- percent discount applies before tax
- discounted amount participates in shipping threshold
- inventory failures still fail

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l2-c1
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `checkout/**, cart/**, pricing/**, inventory/**, shipping/**, docs/contexts/checkout.md`.
