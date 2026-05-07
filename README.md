# AI Coding Workflow Evaluation

[Chinese version](README.zh-CN.md)

This repository is a repeatable benchmark for comparing AI coding workflows on real engineering tasks.

This is not an agent framework or a model leaderboard. It is an evaluation protocol for comparing workflows under repeatable engineering tasks.

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

`--workflow` is a comparison label, not a protocol file. Use it for process labels such as `baseline`, `plan-first`, or `tdd`. Use `run.json.model` for model identity such as `gpt-5.5` or `claude-sonnet-4.5`; do not mix model names into `workflow_id`. The actual execution process is captured by the operator, `transcript.md`, `run.json.process_evidence`, and the collected run evidence.

## Mental Model

```text
task.json + task.md + acceptance.md
        ->
prepare_run creates isolated target worktree
        ->
AI/human coding modifies runs/.../target
        ->
collect_run collects tests, diff, and scope facts
        ->
manual review or llm_review_run writes score.json
        ->
report/dashboard compare workflows and models
```

```text
task      = reusable benchmark case
run       = one workflow/model attempt on one task
score     = review result for that run
dashboard = read-only comparison projection
```

## Quick Start

After adding a public reproducible task under `benchmarks/tasks/`, use the shortcut CLI for the shortest scored loop.

1. Prepare a run and enter its isolated target worktree:

```bash
python scripts/eval.py start --workflow <workflow> --task <task-id> [--model <model>]
cd "$(python scripts/eval.py target)"
```

Run the AI or human workflow against the prepared target worktree. Use the `task.md` copied into the run directory as the coding prompt; use `task.zh-CN.md` if you prefer Chinese. `acceptance.md` stays in the benchmark task directory for review only.

<details>
<summary><strong>Optional:</strong> collect hook-based process evidence</summary>

Run this before starting Claude Code or Codex:

```bash
eval "$(python scripts/eval.py env)"
```

This improves `process_evidence` and link metrics, but the run can be scored without it. See [docs/hooks.md](docs/hooks.md).

</details>

2. After coding finishes, collect test and diff evidence:

```bash
python scripts/eval.py collect
```

<details>
<summary><strong>Optional:</strong> calculate adoption metrics</summary>

If you want line-level adoption metrics, have the AI workflow or reviewer commit the candidate result, then compare that candidate commit with the final accepted commit. This is a link-diagnostic metric only; it does not affect `score.json`.

```bash
cd runs/<workflow>/<task-id>/<run-id>/target
git add .
git commit -m "candidate for <task-id>"
git rev-parse HEAD
```

After the final accepted version exists as a commit:

```bash
python scripts/eval.py adoption \
  --candidate-ref <candidate-sha> \
  --accepted-ref <accepted-sha>
```

`candidate_ref` is the AI candidate commit. `accepted_ref` is the final accepted commit. `target.solution_ref` remains a reference solution and is not used as the default adoption source.

</details>

<details>
<summary><strong>Optional:</strong> inspect reference solution diff</summary>

If the task has `target.solution_ref`, inspect the candidate worktree against the reference implementation before scoring. The helper respects `task.scope.allowed_paths` when present, prints a reviewer-friendly diff view with per-file headers and line numbers, and highlights candidate-side lines with a red background and reference-side lines with a green background.

```bash
python scripts/eval.py solution-diff --color auto
```

This is only context for reviewers; do not score a run by similarity to the reference solution.

</details>

3. Choose one review path before calculating the final score.

Manual path, recommended for the first run: pass the six review scores directly. This creates or updates `score.json` and calculates the final score in one step. Each review value must be from `0.0` to `1.0`. Omit `--manual-hard-gate` unless a reviewer explicitly wants to cap the run:

```bash
python scripts/eval.py score \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6
```

If a manual hard gate is needed, add `--manual-hard-gate public_api_break`. `python scripts/eval.py score --init` is still available for reviewers who prefer editing a draft JSON file by hand.

LLM review path: use an OpenAI-compatible reviewer to create `score.json` and calculate the final score in one step:

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
python scripts/eval.py llm-review
```

For DeepSeek-compatible review, use `AI_EVAL_REVIEW_BASE_URL=https://api.deepseek.com` and pass `--api-key-env DEEPSEEK_API_KEY`.

4. Generate a report or dashboard:

```bash
python scripts/eval.py report
python scripts/eval.py dashboard
```

`report.py` is the quick terminal/Markdown report. `dashboard.py` is a read-only visual comparison board for workflows, models, per-task results, and context link metrics. It writes both `reports/dashboard.html` and `reports/dashboard.zh-CN.html`, and does not modify `run.json`, `score.json`, or review results.

<details>
<summary><strong>Optional:</strong> generate context link metrics</summary>

Generate cross-run context link metrics from hook evidence:

```bash
python scripts/context_metrics.py --runs runs --output reports/context-metrics.json
```

This is a cross-run diagnostic view only. Link metrics require hook events; runs without non-empty `events.jsonl` are excluded from their denominator.

</details>

`scripts/eval.py` does not add a new evaluation protocol. It only remembers the latest run in `runs/.current.json` and resolves `task.json`, `run.json`, and `score.json` paths for you. For parallel experiments, pass `--run-dir runs/<workflow>/<task-id>/<run-id>` to `collect`, `score`, `llm-review`, `solution-diff`, or `adoption`.

## Advanced Low-Level Commands

The shortcut CLI is a thin wrapper around the stable primitives. Use these when debugging, scripting CI, or operating on a run without `runs/.current.json`:

```bash
python scripts/prepare_run.py --workflow <workflow> --task <task-id> [--model <model>]
python scripts/collect_run.py --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python scripts/score_run.py --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --score runs/<workflow>/<task-id>/<run-id>/score.json --set-review correctness=1.0 regression_safety=1.0 maintainability=0.8 test_quality=0.8 security=1.0 process_compliance=0.6 --write
python scripts/llm_review_run.py --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python scripts/report.py --runs runs
python scripts/dashboard.py --runs runs --tasks benchmarks/tasks --output reports/dashboard.html
```

See [examples/go-bugfix-l1-c1](examples/go-bugfix-l1-c1) for a completed end-to-end run.

## Contribute A Task

A useful public benchmark task:

- Comes from a real engineering change
- Uses a fixed public target repository and base commit
- Defines clear expected behavior
- Can be verified by repeatable commands
- Avoids private data, credentials, and local-only setup

Avoid:

- Toy algorithm problems
- Vague product requests
- Tasks only runnable on one person's machine
- Leaking the answer into `task.md`
- Tasks with no repeatable test or review signal

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
reports/                Local generated dashboards and reports, ignored by git
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
