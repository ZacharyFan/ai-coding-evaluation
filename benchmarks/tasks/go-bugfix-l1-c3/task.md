# Task: Lowercase normalized emails

Scenario: customer profile (`customerprofile`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C3_missing, C3: no scenario document exists; infer behavior from code, names, and ordinary tests.

Context:

customerprofile.NormalizeEmail trims but does not lowercase, with no docs available.

Expected behavior:

- local and domain parts are lowercased
- missing @ still errors
- changes stay in customerprofile

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l1-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `customerprofile/**`.
