# Task: Add return preview

Scenario: returns flow (`returns`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C2_partial, C2: `docs/contexts/returns.md` documents the happy path but omits failure and rollback details.

Context:

Add returns.PreviewReturn across order state, refund amount, and inventory policy.

Expected behavior:

- ineligible orders return a reason
- eligible orders return expected refund
- no ledger or inventory side effects

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l2-c2
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `returns/**, orders/**, refunds/**, inventory/**, ledger/**, docs/contexts/returns.md`.
