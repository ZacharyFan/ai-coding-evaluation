## Summary

- 

## Change Type

- [ ] Benchmark task
- [ ] Tooling or CLI
- [ ] Documentation
- [ ] Report or dashboard

## Verification

- [ ] `python -m scripts.validate_task benchmarks/tasks/<task-id>` passes, if this adds or changes a task
- [ ] `python -m scripts.eval registry` was run, if task metadata changed
- [ ] `ruff check scripts tests` passes
- [ ] `ruff format --check scripts tests` passes
- [ ] `python -m pytest` passes

## Data Safety

- [ ] No private code, credentials, tokens, logs, customer data, or non-public repository paths are included
