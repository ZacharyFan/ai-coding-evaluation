# Task Authoring Guide

[Chinese version](task-authoring.zh-CN.md)

An evaluation task is a controlled experiment. The goal is to learn which AI coding workflow produces acceptable changes under repeatable conditions.

## What Makes A Good Task

A good task has five properties:

- Real: taken from a real codebase or a faithful extraction of one
- Fixed: pinned to a target repo and `base_ref`
- Observable: success can be checked through tests, review, or both
- Bounded: the expected diff is limited enough to review
- Fair: every workflow receives the same instructions and starting point

Weak tasks usually fail one of these tests. The most common failure is a vague task that can only be judged by taste.

## Files To Write

Use the closest template in `benchmarks/templates/` as the starting point, then copy it into `benchmarks/tasks/<task-id>`.

`task.md` is the prompt. Write it as the workflow should see it. Include the problem, expected behavior, reproduction steps, and known constraints. Do not include the hidden solution.

`acceptance.md` is for blind review. It should let a reviewer decide whether the final diff is acceptable without knowing which workflow produced it.

`tests.sh` is the required check entry point. It must be executable and deterministic. Prefer checks that fail before the task is solved, but regression checks are also useful when the defect cannot be safely reproduced in a short script.

`task.json` is the contract. It describes the target repo, budget, complexity, required tests, hidden checks, and scoring weights.

## Choosing Size And Complexity

Use `effort_size` for work size:

```text
small    Localized change, usually one behavior or one narrow test gap
medium   Several files, investigation, or a modest feature/refactor
large    Broad implementation, migration, or multiple connected changes
```

Use `business_complexity` for reasoning difficulty:

```text
L1_standardized  Standard pattern, simple state, direct mapping from task to code
L2_linked        Multiple states, linked fields, integrations, or multi-step behavior
L3_complex       Custom architecture, deep UI/state behavior, complex data flow
```

Use `context_maturity` for whether the agent has enough project knowledge:

```text
C1_complete      Relevant docs, examples, APIs, and conventions are findable
C2_partial       Some context exists, but it is scattered, stale, or incomplete
C3_missing       The agent must infer important context or create missing structure
```

These dimensions are intentionally separate. A dependency update can be large but low-complexity. A one-line authorization condition can be small but high-complexity.

## Writing Hidden Checks

Hidden checks should protect against shortcuts, not reveal the answer.

Good:

```text
The fix is implemented at the source of the behavior, not by special-casing the visible test.
No public API behavior changes beyond the requested behavior.
The solution handles empty and multi-item inputs.
```

Weak:

```text
Change function parseUserInput in src/parser.ts.
Use exactly this SQL query.
Make it better.
```

## Anti-Patterns

Reject or rewrite tasks with:

- No fixed `base_ref`
- Private context that is not available to the agent
- Acceptance criteria based only on subjective taste
- Tests that pass regardless of the implementation
- A task that requires production credentials or live customer data
- A huge migration disguised as `small`
- Hidden checks that encode the solution path instead of the desired behavior

## Local Validation

Run both commands before opening a PR:

```bash
python scripts/validate_task.py benchmarks/tasks/<task-id>
pytest
```

The first command validates the task contribution. The second command protects the benchmark tooling itself.

Templates are validated explicitly with:

```bash
python scripts/validate_task.py benchmarks/templates
```
