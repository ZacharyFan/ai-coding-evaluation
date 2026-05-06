# Task: Add customer display names

Scenario: customer profile (`customerprofile`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C3_missing, C3: no scenario document exists; infer behavior from code, names, and ordinary tests.

Context:

Add customerprofile.DisplayName from profile name fields.

Expected behavior:

- uses FirstName + LastName first
- falls back to Email when names are missing
- empty profile returns anonymous

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l1-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `customerprofile/**`.
