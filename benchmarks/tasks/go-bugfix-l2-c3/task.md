# Task: Block subscriptions for held accounts

Scenario: subscription activation (`subscriptions`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C3_missing, C3: no subscription context document exists; infer from account/billing/entitlement code.

Context:

subscriptions.Activate ignores account.Hold and still bills/enables entitlement.

Expected behavior:

- held accounts return an error
- no invoice is created
- no entitlement is activated

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `subscriptions/**, account/**, billing/**, entitlement/**`.
