# Go Bugfix Example

[简体中文](README.zh-CN.md)

This is an end-to-end example. It shows what a completed evaluation run looks like after task definition, workflow execution, evidence collection, review, and scoring.

It is not a live `runs/` directory. Local run evidence belongs under `runs/`, which is ignored by git.

## Scenario

The official benchmark task targets the public Go demo repository:

```text
https://github.com/ZacharyFan/ai-coding-evaluation-demo-golang.git
```

The benchmark task asks the workflow to fix `cart.ApplyDiscount` so it rejects invalid discount percentages below `0` or above `100`.

## Files

```text
task/   Copy of the benchmark task definition
run/    Copy of completed run evidence
```

The run evidence demonstrates:

```text
transcript.md   Summary of the workflow and target commits
diff.patch      Final target-project diff
test.log        Captured test command output
run.json        Pre-scoring run facts
score.json      Review scores, structured review notes, and final score
```

## Reproduce The Shape

A real local run uses `runs/`, not this example directory. `prepare_run.py` clones the public target repo into `runs/.../target` before the workflow starts:

In this example, `baseline` is just the workflow group label used for run paths and report aggregation.

```bash
python scripts/prepare_run.py --workflow baseline --task go-bugfix-001 --run-id demo-002
python scripts/execute_run.py \
  --task benchmarks/tasks/go-bugfix-001/task.json \
  --run runs/baseline/go-bugfix-001/demo-002/run.json \
  --write
python scripts/score_run.py \
  --run runs/baseline/go-bugfix-001/demo-002/run.json \
  --score runs/baseline/go-bugfix-001/demo-002/score.json \
  --init \
  --write
python scripts/score_run.py \
  --task benchmarks/tasks/go-bugfix-001/task.json \
  --run runs/baseline/go-bugfix-001/demo-002/run.json \
  --score runs/baseline/go-bugfix-001/demo-002/score.json \
  --write
python scripts/report.py --runs runs
```
