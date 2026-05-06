# Task: Round tax to the nearest cent

Scenario: tax rules (`taxrules`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C2_partial, C2: `docs/contexts/taxrules.md` is partial and omits rounding and cap boundaries.

Context:

taxrules.TaxCents truncates half-cent tax; partial docs omit rounding details.

Expected behavior:

- half-cent and above rounds up
- exact-cent tax stays unchanged
- invalid rates still error

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `taxrules/**, docs/contexts/taxrules.md`.
