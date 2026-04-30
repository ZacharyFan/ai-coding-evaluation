# AI Coding Workflow Evaluation

[Chinese version](README.zh-CN.md)

This repository is a repeatable benchmark for comparing AI coding workflows on real engineering tasks.

The core question is not "can the AI write code?" It is:

```text
Which workflow produces acceptable changes with the least human attention?
```

The primary unit is:

```text
accepted change / human attention minute
```

## How It Works

Each benchmark task defines:

- A fixed target repository and `base_ref`
- A task prompt, acceptance criteria, required checks, and hidden review checks
- Budget limits for time, human intervention, and cost
- Metadata for work size and complexity
- Scoring weights for review and efficiency

Each workflow runs the same task from the same starting point. A run preserves evidence in `runs/`: transcript, diff, test log, review notes, and normalized metrics. The scorer combines blind-review dimensions with efficiency, then applies hard gates for unsafe or incomplete work.

## Quick Start

After adding a real task under `benchmarks/tasks/`, create a run evidence folder:

```bash
python scripts/run_task.py --workflow baseline --task <task-id>
```

Score a run:

```bash
python scripts/score_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/baseline/<task-id>/latest/metrics.json \
  --write
```

Generate a report:

```bash
python scripts/report.py --runs runs
```

Validate benchmark tasks and tooling:

```bash
python scripts/validate_task.py
pytest
```

## Contribute A Task

Copy the closest task-type template:

```bash
cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
```

Then edit `task.json`, `task.md`, `acceptance.md`, and `tests.sh`.

Before opening a PR:

```bash
python scripts/validate_task.py benchmarks/tasks/<task-id>
pytest
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the PR path and [docs/task-authoring.md](docs/task-authoring.md) for how to write a useful evaluation task.

## Repository Layout

```text
benchmarks/tasks/       Real benchmark tasks that participate in runs and reports
benchmarks/templates/   Copyable task-authoring templates that are not run by default
workflows/              Workflow definitions to compare
runs/                   Per-workflow, per-task run evidence
schemas/                JSON schemas for task, workflow, and run files
scripts/                Zero-dependency helpers for validation, scoring, and reports
tests/                  Unit tests for the evaluation tooling
docs/                   Evaluation method, rubric, and task-authoring docs
```

## Scoring Model

Default weighted score:

```text
correctness          35
regression_safety    15
maintainability      15
test_quality         10
security             10
process_compliance    5
efficiency           10
```

Hard gates cap the final score:

```text
task_not_solved          max 40
security_issue           max 50
public_api_break         max 55
required_tests_failed    max 60
unrelated_changes        max 65
hidden_tests_failed      max 70
```

See [docs/evaluation-method.md](docs/evaluation-method.md) for the metric model and [docs/rubric.md](docs/rubric.md) for review scoring.

## Task Type Templates

This repository currently ships task-type templates, not real benchmark tasks:

```text
bugfix      Fix a real defect
feature     Add a small feature
refactor    Improve structure without behavior change
test        Add missing test coverage
frontend    Improve a UI or integration flow
```

Real tasks belong in `benchmarks/tasks/`. Templates stay in `benchmarks/templates/` and do not participate in default runs or reports.

Decision confidence:

```text
5 tasks      80% useful for debugging the benchmark, 30% useful for choosing a workflow
10-15 tasks  60% useful for eliminating weak workflows
30+ tasks    75% useful for selecting a main workflow
```
