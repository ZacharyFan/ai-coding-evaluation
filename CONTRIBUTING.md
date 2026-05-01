# Contributing Evaluation Tasks

[Chinese version](CONTRIBUTING.zh-CN.md)

This project needs repeatable engineering tasks, not prompts that merely sound realistic.

## Contribution Path

1. Copy the closest task-type template:

   ```bash
   cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
   ```

2. Rename the task id in `task.json` to match the new directory name.
3. Replace `task.md`, `acceptance.md`, and `tests.sh` with a concrete task from a public, cloneable repository.
4. Validate locally:

   ```bash
   python scripts/validate_task.py benchmarks/tasks/<task-id>
   pytest
   ```

## Task Directory Contract

Every task directory must contain:

```text
task.json       Machine-readable metadata, budget, target repo, checks, and `scoring_weights`
task.md         The task prompt shown to the workflow
acceptance.md   Human-readable acceptance criteria for blind review
tests.sh        Deterministic required checks, executable with ./tests.sh
```

Optional localized files such as `task.zh-CN.md` and `acceptance.zh-CN.md` are welcome when they help reviewers.

`benchmarks/tasks/` is the public benchmark set. Templates live under `benchmarks/templates/` and are not run by default. Private or local experiments belong under `benchmarks/local/`, which is ignored by git.

## Naming

Use a stable, descriptive id:

```text
bugfix-002
feature-003
refactor-002
test-002
frontend-002
integration-001
ci-001
```

The `id` in `task.json` must equal the directory name.

## Required Metadata

Set `effort_size` by work size:

```text
small    Fits in a narrow, localized change
medium   Touches a few files or requires meaningful investigation
large    Broad change with budget pressure
```

Set complexity separately:

```text
business_complexity
  L1_standardized  Direct bugfix, simple CRUD, config, straightforward tests
  L2_linked        Cross-field state, multi-step flow, integration, linked data
  L3_complex       Architecture, deep custom UI, complex data flow or reasoning

context_maturity
  C1_complete      Docs, APIs, examples, and project knowledge are enough
  C2_partial       Context exists but is incomplete, stale, or scattered
  C3_missing       The agent must infer or create missing context
```

`effort_size` is not complexity. A task can be small and complex, or large and mechanical.

## Acceptance Bar

A good public task has:

- A cloneable Git URL in `target.repo`
- A full commit SHA in `target.base_ref`
- Reproduction or entry point precise enough for another person to rerun
- Required checks that fail before the change or protect the desired behavior
- Hidden checks that describe reviewer concerns without leaking the solution
- No private context that the agent cannot inspect
- No subjective-only acceptance criteria

## PR Checklist

Before opening a PR:

- `python scripts/validate_task.py benchmarks/tasks/<task-id>` passes
- `pytest` passes
- `tests.sh` is executable
- The task can be run from a clean checkout of the public target repo
- `scoring_weights` still sums to 100
- The contribution does not include private code, credentials, tokens, logs, or customer data

GitHub, GitLab, and generic Git remotes are supported through standard clone URLs. Private business repositories can be useful for local experiments, but they are not acceptable as public benchmark task targets.
