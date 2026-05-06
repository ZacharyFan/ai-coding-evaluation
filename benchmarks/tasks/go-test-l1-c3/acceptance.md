# Acceptance: Test deleted profiles cannot receive marketing

Public acceptance:

- adds TestCanSendMarketingRejectsDeletedProfiles
- covers opted-in but deleted profiles
- does not require production changes

Hidden checks:

- The named test uses public customerprofile APIs.
- C3 remains undocumented.

Required command:

```bash
./scripts/run_eval_case.sh go-test-l1-c3
```
