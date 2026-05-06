# Task: Extract profile validation helper

Scenario: customer profile (`customerprofile`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C3_missing, C3: no scenario document exists; infer behavior from code, names, and ordinary tests.

Context:

customerprofile.Validate should split field validation into internal helpers.

Expected behavior:

- adds validateProfileIdentity helper
- Validate calls the helper
- behavior stays unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l1-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `customerprofile/**`.
