# Rubric

[Chinese version](rubric.zh-CN.md)

Use this rubric during blind review. Reviewers should not know which workflow produced the run.

## Correctness

```text
1.0 Fully solves the task and handles stated edge cases
0.7 Solves the common path but has minor edge case gaps
0.4 Partially solves the task
0.0 Does not solve the task
```

## Regression Safety

```text
1.0 Existing behavior preserved, relevant tests pass, no API/UX break
0.7 Low-risk changes with minor uncertainty
0.4 Meaningful regression risk or weak evidence
0.0 Known breakage
```

## Maintainability

```text
1.0 Simple, localized, idiomatic, easy to review
0.7 Reasonable but has avoidable complexity
0.4 Hard to maintain or broad diff
0.0 Unreadable or brittle
```

## Test Quality

```text
1.0 Tests cover core behavior and likely future regressions
0.7 Tests cover the main path
0.4 Shallow tests or weak assertions
0.0 No meaningful tests
```

## Security

```text
1.0 No security concerns found
0.7 Minor hardening opportunity
0.4 Meaningful unresolved risk
0.0 Vulnerability introduced
```

## Process Compliance

This is a stability signal, not a substitute for correctness. It captures whether the agent worked in a way that is likely to reproduce on harder tasks.

```text
1.0 Used the right project instructions, docs, tools, and self-review trail
0.7 Mostly followed the expected workflow, with incomplete evidence
0.4 Code may be right, but process evidence is weak or accidental
0.0 Ignored key project instructions, docs, tools, or review requirements
```

## Efficiency

Calculated from task budgets:

```text
duration_minutes
human_interventions
cost_usd
```

Staying under budget scores near `1.0`; exceeding budget decays proportionally.
