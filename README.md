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

- A fixed target repository, `base_ref`, and optional reference-only `solution_ref`
- A task prompt, acceptance criteria, required checks, and hidden review checks
- Budget limits for time, human intervention, and cost
- Metadata for work size and complexity
- A `scoring_weights` object for review and efficiency

Each workflow runs the same task from the same starting point. Public tasks point at cloneable target repositories and fixed commit SHAs. Optional `target.solution_ref` values are reference implementations for authors and reviewers; they are not the only acceptable solution and are not used by the tooling. A run preserves facts in `run.json` and scoring results in `score.json`, alongside transcript, diff, and test log evidence.

`--workflow` is a comparison label, not a protocol file. Use any stable label such as `baseline`, `codex`, `claude`, `plan-first`, or `tdd` to group runs. The actual execution process is captured by the operator, `transcript.md`, `run.json.process_evidence`, and the collected run evidence.

## Quick Start

After adding a public reproducible task under `benchmarks/tasks/`, prepare an isolated target worktree:

```bash
python scripts/prepare_run.py --workflow <workflow> --task <task-id>
```

Run the AI or human workflow against the prepared `runs/.../target` worktree. Use `runs/<workflow>/<task-id>/<run-id>/task.md` as the coding prompt; use `task.zh-CN.md` if you prefer Chinese. `acceptance.md` stays in the benchmark task directory for review only.

For optional hook-based process evidence with Claude Code or Codex, export the `AI_EVAL_*` variables printed by `prepare_run.py`, start the agent from `runs/.../target`, and see [docs/hooks.md](docs/hooks.md).

After coding finishes, collect test and diff evidence:

```bash
python scripts/execute_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --write
```

Optional review aid: if the task has `target.solution_ref`, inspect the candidate worktree against the reference implementation before scoring. The helper respects `task.scope.allowed_paths` when present, prints a reviewer-friendly diff view with per-file headers and line numbers, and highlights candidate-side lines with a red background and reference-side lines with a green background. This is only context for reviewers; do not score a run by similarity to the reference solution.

```bash
python scripts/show_solution_diff.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --color auto
```

Choose one review path before calculating the final score.

Manual path: pass the six review scores directly. This creates or updates `score.json` and calculates the final score in one step. Each review value must be from `0.0` to `1.0`. Omit `--manual-hard-gate` unless a reviewer explicitly wants to cap the run:

```bash
python scripts/score_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
  --score runs/<workflow>/<task-id>/<run-id>/score.json \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6 \
  --write
```

If a manual hard gate is needed, add `--manual-hard-gate public_api_break`. `score_run.py --init` is still available for reviewers who prefer editing a draft JSON file by hand.

LLM path: use an OpenAI-compatible reviewer to create `score.json` and calculate the final score in one step:

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
python scripts/llm_review_run.py \
  --task benchmarks/tasks/<task-id>/task.json \
  --run runs/<workflow>/<task-id>/<run-id>/run.json \
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

Then edit `task.json`, especially `target`, optional `target.solution_ref`, and `scope.allowed_paths`, plus `task.md`, `acceptance.md`, and `tests.sh`.

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
integrations/           Optional Claude Code and Codex hook templates
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
