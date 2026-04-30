# AI Coding Workflow Evaluation

[Chinese version](README.zh-CN.md)

This repository is a test bench for comparing AI coding workflows on repeatable engineering tasks.

The unit of evaluation is not "did the AI write code." It is:

```text
accepted change / human attention minute
```

## Repository Layout

```text
benchmarks/tasks/   Task specs, acceptance criteria, checks, and scoring weights
workflows/          Workflow definitions to compare
runs/               Per-workflow, per-task run evidence
schemas/            JSON schemas for task, workflow, and run files
scripts/            Zero-dependency helpers for creating runs, scoring, and reporting
tests/              Unit tests for the evaluation tooling
docs/               Evaluation method and rubric docs
```

See [docs/multi-language-targets.md](docs/multi-language-targets.md) for Python, TypeScript, Go, Rust, and other target project examples.

## First Calibration Set

The initial benchmark set has five task templates:

```text
bugfix-001     Fix a real defect
feature-001    Add a small feature
refactor-001   Improve structure without behavior change
test-001       Add missing test coverage
frontend-001   Improve a UI or integration flow
```

These are intentionally templates. Replace each `task.md`, `acceptance.md`, and `tests.sh` with concrete tasks from real repos before trusting the scores.

## Quick Start

Create a run evidence folder:

```bash
python scripts/run_task.py --workflow baseline --task bugfix-001
```

Score a run:

```bash
python scripts/score_run.py \
  --task benchmarks/tasks/bugfix-001/task.json \
  --run runs/baseline/bugfix-001/latest/metrics.json \
  --write
```

Generate a report:

```bash
python scripts/report.py --runs runs
```

Run tests:

```bash
pytest
```

## Hard Gates

Hard gates clamp the final score. This prevents a fast but unsafe workflow from looking good.

```text
task_not_solved          max score 40
security_issue           max score 50
public_api_break         max score 55
required_tests_failed    max score 60
unrelated_changes        max score 65
hidden_tests_failed      max score 70
```

## Decision Rule

Use five tasks only to calibrate the benchmark. Use 10-15 tasks to eliminate bad workflows. Use 30+ tasks to select a main workflow.
