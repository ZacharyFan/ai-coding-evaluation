# Task: Extract return eligibility decision

Scenario: returns flow (`returns`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C2_partial, C2: `docs/contexts/returns.md` documents the happy path but omits failure and rollback details.

Context:

returns.ProcessReturn eligibility logic should be extracted.

Expected behavior:

- adds returnEligibilityReason
- ProcessReturn and PreviewReturn reuse it
- behavior stays unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `returns/**, orders/**, refunds/**, inventory/**, ledger/**, docs/contexts/returns.md`.
