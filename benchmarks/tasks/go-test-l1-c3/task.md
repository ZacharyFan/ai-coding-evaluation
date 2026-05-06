# Task: Test deleted profiles cannot receive marketing

Scenario: customer profile (`customerprofile`).

- Business complexity: L1_standardized, single-domain model in one package/aggregate.
- Context maturity: C3_missing, C3: no scenario document exists; infer behavior from code, names, and ordinary tests.

Context:

customerprofile.CanSendMarketing lacks Deleted=true coverage.

Expected behavior:

- adds TestCanSendMarketingRejectsDeletedProfiles
- covers opted-in but deleted profiles
- does not require production changes

Reproduction:

```bash
./scripts/run_eval_case.sh go-test-l1-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `customerprofile/**`.
