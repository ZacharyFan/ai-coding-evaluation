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

## Why Not A Model Leaderboard?

Model leaderboards answer "which model scored higher on a fixed test?" This project answers a messier engineering question:

```text
Which workflow produces acceptable changes with the least human attention on my task distribution?
```

The benchmark keeps quality evidence, process evidence, and delivery evidence separate. A stronger model can still lose if the workflow needs constant steering, skips project context, or produces changes that do not survive review.

## What Ships In This Repo

- 36 executable Go benchmark tasks under `benchmarks/tasks/`
- Copyable task templates under `benchmarks/templates/`
- A scored end-to-end demo under `examples/go-bugfix-l1-c1/`
- Zero-runtime-dependency Python CLI helpers in `scripts/`
- Optional Codex and Claude Code hook templates under `integrations/`
- English and Chinese docs, schemas, reports, and dashboard generation

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

## Install

Requirements for the CLI and demo:

```text
Python 3.11+
Git
```

Install from a checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ai-eval doctor
```

Every `ai-eval ...` command can also be run as `python -m scripts.eval ...` from the repository root. `bin/ai-eval` remains available for shell workflows that need an absolute repo helper.

## Quick Start

### 2-Minute Demo

This path needs no API key and no live AI coding session. It copies the committed scored example into ignored local `runs/` evidence, then renders the normal report and dashboard.

```bash
ai-eval demo
ai-eval report --runs runs
ai-eval dashboard --runs runs --tasks benchmarks/tasks
```

Open `reports/dashboard.html` or `reports/dashboard.zh-CN.html` to inspect the visual board. The demo is idempotent; use `ai-eval demo --reset` to rebuild `runs/demo/go-bugfix-l1-c1/example`.

### 10-Minute Live Run

Requirements: Git, Python 3.11+, and Go.

```bash
ai-eval start --workflow baseline --task go-bugfix-l1-c1 --model <model>
eval "$(ai-eval env)"
cd "$AI_EVAL_TARGET_WORKTREE"
```

Run your AI or human workflow in the target worktree. Use the `task.md` copied into the run directory as the coding prompt; use `task.zh-CN.md` if you prefer Chinese. `acceptance.md` stays reviewer-only in the benchmark task directory.

After coding finishes:

```bash
ai-eval collect
ai-eval score \
  --set-review \
    correctness=1.0 \
    regression_safety=1.0 \
    maintainability=0.8 \
    test_quality=0.8 \
    security=1.0 \
    process_compliance=0.6
ai-eval report --runs runs
ai-eval dashboard --runs runs --tasks benchmarks/tasks
```

### Contribute A Task

```bash
cp -R benchmarks/templates/bugfix benchmarks/tasks/bugfix-002
python -m scripts.validate_task benchmarks/tasks/bugfix-002
ai-eval registry
ruff check scripts tests
ruff format --check scripts tests
python -m pytest
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the PR path and [docs/task-authoring.md](docs/task-authoring.md) for how to write a useful evaluation task.

## Advanced Evidence

Use these optional evidence paths when you need deeper process, review, or comparison data without making the Quick Start heavier.

<details>
<summary><strong>Optional:</strong> browse available tasks before starting a run</summary>

Generate the bilingual task registry when you want to browse task metadata before choosing a run:

```bash
ai-eval registry
```

`benchmark_registry.py` writes `benchmarks/index.html` and `benchmarks/index.zh-CN.html`. It is a language-agnostic catalog of executable tasks under `benchmarks/tasks/`; it describes task metadata and entrypoints, not run results.

</details>

<details>
<summary><strong>Optional:</strong> collect hook-based process evidence</summary>

Hook evidence improves `process_evidence` and context link metrics. Before starting Claude Code or Codex:

```bash
eval "$(ai-eval env)"
ai-eval hooks
```

If untracked hook files already exist, use `ai-eval hooks --merge`. Tracked hook files are never modified.

The agent must be started from the same shell so it inherits `AI_EVAL_*`. Hooks improve evidence, but the run can be scored without them. See [docs/hooks.md](docs/hooks.md).

</details>

<details>
<summary><strong>Optional:</strong> calculate adoption metrics</summary>

For line-level adoption metrics, have the workflow or reviewer commit the candidate result, then compare that candidate commit with the final accepted commit:

```bash
ai-eval adoption --candidate-ref <candidate-sha> --accepted-ref <accepted-sha>
```

`candidate_ref` is the AI candidate commit. `accepted_ref` is the final accepted commit. `target.solution_ref` remains a reference solution and is not used as the default adoption source.

</details>

<details>
<summary><strong>Optional:</strong> inspect reference solution diff</summary>

If the task has `target.solution_ref`, inspect candidate-vs-reference context before scoring:

```bash
ai-eval solution-diff --color auto
```

This is reviewer context only; do not score a run by similarity to the reference solution.

</details>

<details>
<summary><strong>Optional:</strong> use LLM review</summary>

LLM review can create `score.json` through an OpenAI-compatible reviewer:

```bash
AI_EVAL_REVIEW_MODEL=<model> \
AI_EVAL_REVIEW_BASE_URL=https://api.openai.com/v1 \
ai-eval llm-review
```

For DeepSeek-compatible review, use `AI_EVAL_REVIEW_BASE_URL=https://api.deepseek.com` and pass `--api-key-env DEEPSEEK_API_KEY`.

</details>

<details>
<summary><strong>Optional:</strong> generate context link metrics</summary>

Cross-run context link metrics are generated from hook evidence:

```bash
python -m scripts.context_metrics --runs runs --output reports/context-metrics.json
```

This is a cross-run diagnostic view only. Link metrics require hook events; runs without non-empty `events.jsonl` are excluded from their denominator.

</details>

The shortcut CLI does not add a new evaluation protocol. It only remembers the latest run in `runs/.current.json` and resolves `task.json`, `run.json`, and `score.json` paths for you. For parallel experiments, pass `--run-dir runs/<workflow>/<task-id>/<run-id>` to `collect`, `score`, `llm-review`, `solution-diff`, or `adoption`.

## Advanced Low-Level Commands

The shortcut CLI is a thin wrapper around the stable primitives. Use these when debugging, scripting CI, or operating on a run without `runs/.current.json`:

<details>
<summary>Show low-level primitive commands</summary>

```bash
python -m scripts.prepare_run --workflow <workflow> --task <task-id> [--model <model>]
python -m scripts.collect_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python -m scripts.score_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --score runs/<workflow>/<task-id>/<run-id>/score.json --set-review correctness=1.0 regression_safety=1.0 maintainability=0.8 test_quality=0.8 security=1.0 process_compliance=0.6 --write
python -m scripts.llm_review_run --task benchmarks/tasks/<task-id>/task.json --run runs/<workflow>/<task-id>/<run-id>/run.json --write
python -m scripts.report --runs runs
python -m scripts.dashboard --runs runs --tasks benchmarks/tasks --output reports/dashboard.html
python -m scripts.benchmark_registry --tasks benchmarks/tasks --output benchmarks/index.html
```

</details>

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
python -m scripts.validate_task benchmarks/tasks/<task-id>
ruff check scripts tests
ruff format --check scripts tests
python -m pytest
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the PR path and [docs/task-authoring.md](docs/task-authoring.md) for how to write a useful evaluation task.

## Repository Health Checks

Use these checks when changing benchmark tasks, templates, schemas, scripts, or docs:

```bash
python -m scripts.validate_task
python -m scripts.eval registry
ruff check scripts tests
ruff format --check scripts tests
python -m pytest
```

These commands validate the benchmark repository itself. They are maintenance and contribution gates, not the scoring path for one workflow run.

## Repository Layout

```text
benchmarks/tasks/       Real benchmark tasks that participate in runs and reports
benchmarks/index.html   Generated bilingual task registry entrypoint
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

This repository ships executable Go benchmark tasks plus task-type templates:

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
