# Task: Name the basis-points denominator

Scenario: tax rules (`taxrules`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C2_partial, C2: `docs/contexts/taxrules.md` is partial and omits rounding and cap boundaries.

Context:

taxrules uses raw 10000; replace it with a named constant.

Expected behavior:

- adds BasisPointsDenominator
- tax code uses the constant
- behavior stays unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `taxrules/**, docs/contexts/taxrules.md`.
