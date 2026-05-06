# Acceptance: Extract return eligibility decision

Public acceptance:

- adds returnEligibilityReason
- ProcessReturn and PreviewReturn reuse it
- behavior stays unchanged

Hidden checks:

- Eligibility spans order state and refund policy.
- No external API is removed.

Required command:

```bash
./scripts/run_eval_case.sh go-refactor-l2-c2
```
