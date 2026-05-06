# Task: Extract subscription activation decision

Scenario: subscription activation (`subscriptions`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C3_missing, C3: no subscription context document exists; infer from account/billing/entitlement code.

Context:

subscriptions.Activate should extract account/billing/entitlement decision logic.

Expected behavior:

- adds activationDecision helper
- Activate calls it
- behavior stays unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `subscriptions/**, account/**, billing/**, entitlement/**`.
