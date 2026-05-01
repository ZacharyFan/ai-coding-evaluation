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
- A `scoring_weights` object for review and efficiency

Each workflow runs the same task from the same starting point. Public tasks point at cloneable target repositories and fixed commit SHAs. A run preserves facts in `run.json` and scoring results in `score.json`, alongside transcript, diff, and test log evidence.

`--workflow` is a comparison label, not a protocol file. Use names such as `baseline`, `plan-first`, or `tdd` to group runs. The actual execution process is captured by the operator, `transcript.md`, `run.json.process_evidence`, and the collected run evidence.

## Quick Start

After adding a public reproducible task under `benchmarks/tasks/`, prepare an isolated target worktree:

```bash
python scripts/prepare_run.py --workflow baseline --task <task-id>
```

Run the AI or human workflow against the prepared `runs/.../target` worktree, then collect test and diff evidence:

```bash
python scripts/execute_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/baseline/<task-id>/<run-id>/run.json \
  --write
```

For manual review, initialize a draft score file, fill `score.json`, then calculate final score fields:

```bash
python scripts/score_run.py \
  --run runs/baseline/<task-id>/<run-id>/run.json \
  --score runs/baseline/<task-id>/<run-id>/score.json \
  --init \
  --write

python scripts/score_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/baseline/<task-id>/<run-id>/run.json \
  --score runs/baseline/<task-id>/<run-id>/score.json \
  --write
```

Optionally, use an OpenAI-compatible LLM reviewer to create `score.json`:

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
python scripts/llm_review_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/baseline/<task-id>/<run-id>/run.json \
  --write
```

For DeepSeek-compatible review, use `AI_EVAL_REVIEW_BASE_URL=https://api.deepseek.com` and pass `--api-key-env DEEPSEEK_API_KEY`.

Generate a report:

```bash
python scripts/report.py --runs runs
```

See [examples/go-bugfix-001](examples/go-bugfix-001) for a completed end-to-end run.

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

## Repository Health Checks

Use these checks when changing benchmark tasks, templates, schemas, scripts, or docs:

```bash
python scripts/validate_task.py
pytest
```

These commands validate the benchmark repository itself. They are maintenance and contribution gates, not the scoring path for one workflow run.

## Repository Layout

```text
benchmarks/tasks/       Real benchmark tasks that participate in runs and reports
benchmarks/local/       Private local experiment tasks, ignored by git
benchmarks/templates/   Copyable task-authoring templates that are not run by default
runs/                   Local run evidence and target worktrees, ignored by git
examples/               Curated example tasks and run evidence
schemas/                JSON schemas for task, run, and score files
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

Public reproducible tasks belong in `benchmarks/tasks/`. They must use a cloneable Git URL and a full commit SHA. Private or local experiments belong in `benchmarks/local/`. Templates stay in `benchmarks/templates/` and do not participate in default runs or reports.

Decision confidence:

```text
5 tasks      80% useful for debugging the benchmark, 30% useful for choosing a workflow
10-15 tasks  60% useful for eliminating weak workflows
30+ tasks    75% useful for selecting a main workflow
```
