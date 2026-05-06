# Acceptance: Block subscriptions for held accounts

Public acceptance:

- held accounts return an error
- no invoice is created
- no entitlement is activated

Hidden checks:

- The fix coordinates account, billing, and entitlement.
- No C3 context doc is introduced.

Required command:

```bash
./scripts/run_eval_case.sh go-bugfix-l2-c3
```
