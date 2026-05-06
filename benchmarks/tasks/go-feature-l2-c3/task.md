# Task: Add subscription plan-change preview

Scenario: subscription activation (`subscriptions`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C3_missing, C3: no subscription context document exists; infer from account/billing/entitlement code.

Context:

Add subscriptions.PreviewPlanChange across account, billing, and entitlement.

Expected behavior:

- requires active entitlement
- returns prorated credit and next charge
- held accounts cannot preview

Reproduction:

```bash
./scripts/run_eval_case.sh go-feature-l2-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `subscriptions/**, account/**, billing/**, entitlement/**`.
