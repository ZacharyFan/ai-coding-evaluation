# Acceptance Criteria

- `go test ./...` passes in `ai-coding-evaluation-demo-golang`.
- `ApplyDiscount` rejects discount percentages below 0.
- `ApplyDiscount` rejects discount percentages above 100.
- Valid discount calculations still return the expected discounted total.
- Negative total validation still returns an error.
- The final diff does not include unrelated cleanup.
