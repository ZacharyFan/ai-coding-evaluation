# Task: Test tax-rate cap

Scenario: tax rules (`taxrules`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C2_partial, C2: `docs/contexts/taxrules.md` is partial and omits rounding and cap boundaries.

Context:

taxrules.ValidateRule lacks cap-overflow coverage.

Expected behavior:

- adds TestValidateRuleRejectsRateAboveCap
- covers 2501 basis points
- does not change production behavior

Reproduction:

```bash
./scripts/run_eval_case.sh go-test-l1-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `taxrules/**, docs/contexts/taxrules.md`.
