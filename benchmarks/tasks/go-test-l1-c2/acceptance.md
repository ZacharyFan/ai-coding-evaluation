# Acceptance: Test tax-rate cap

Public acceptance:

- adds TestValidateRuleRejectsRateAboveCap
- covers 2501 basis points
- does not change production behavior

Hidden checks:

- A named test protects the cap.
- The test uses the taxrules package only.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l1-c2
```
