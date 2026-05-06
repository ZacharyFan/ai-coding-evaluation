# Task: Make reconciliation notifications idempotent

Scenario: settlement reconciliation (`settlement_reconciliation`).

- Business complexity: L3_complex, distributed transaction or cross-service flow with interfaces, compensation, idempotency, or outbox.
- Context maturity: C3_missing, C3: no reconciliation context document exists; infer from service interfaces and tests.

Context:

settlement_reconciliation.Reconcile sends duplicate notifications when rerunning the same batch.

Expected behavior:

- same-batch discrepancies notify once
- different batches can still notify
- matching results stay unchanged

Reproduction:

```bash
./scripts/run_eval_case.sh go-bugfix-l3-c3
```

Constraints:

- Do not special-case tests.
- Keep existing public APIs compatible unless this task explicitly asks for a new API.
- Keep the diff within `settlement_reconciliation/**`.
