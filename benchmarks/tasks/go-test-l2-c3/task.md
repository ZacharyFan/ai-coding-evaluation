# Task: Test successful subscription activation

Scenario: subscription activation (`subscriptions`).

- Business complexity: L2_linked, multi-domain model coordination across at least three domain packages.
- Context maturity: C3_missing, C3: no subscription context document exists; infer from account/billing/entitlement code.

Context:

subscriptions lacks happy-path coverage spanning account/billing/entitlement.

Expected behavior:

- adds TestActivateCreatesInvoiceAndEntitlement
- covers invoice creation and entitlement activation
- does not require production changes

Reproduction:

```bash
./scripts/run_eval_case.sh go-test-l2-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `subscriptions/**, account/**, billing/**, entitlement/**`.
