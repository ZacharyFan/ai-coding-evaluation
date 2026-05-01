# Multi-Language Targets

[Chinese version](multi-language-targets.zh-CN.md)

The benchmark is language-agnostic. A task describes the target repo, fixed base revision, setup commands, and test commands.

## Target Metadata

Each `task.json` can include:

```json
{
  "target": {
    "repo": "https://github.com/owner/repo.git",
    "base_ref": "full-commit-sha",
    "language": "typescript",
    "package_manager": "pnpm",
    "setup_commands": ["pnpm install"],
    "test_commands": ["pnpm test", "pnpm lint"],
    "working_directory": "."
  }
}
```

`base_ref` matters. Without a fixed starting revision, two workflow runs are not really comparable. Public benchmark tasks under `benchmarks/tasks/` must use a cloneable Git URL and a full commit SHA. Local filesystem paths are reserved for `benchmarks/local/` experiments and templates.

## Examples

Python:

```json
{
  "target": {
    "repo": "https://github.com/example/target-python-app.git",
    "base_ref": "9f3c2a1d4b5e6f708192a3b4c5d6e7f8091a2b3c",
    "language": "python",
    "package_manager": "uv",
    "setup_commands": ["uv sync"],
    "test_commands": ["uv run pytest", "uv run ruff check ."],
    "working_directory": "."
  }
}
```

TypeScript:

```json
{
  "target": {
    "repo": "https://gitlab.com/example/target-web-app.git",
    "base_ref": "4b8d10c0a1b2c3d4e5f60718293a4b5c6d7e8f90",
    "language": "typescript",
    "package_manager": "pnpm",
    "setup_commands": ["pnpm install --frozen-lockfile"],
    "test_commands": ["pnpm test", "pnpm lint", "pnpm exec playwright test"],
    "working_directory": "."
  }
}
```

Go:

```json
{
  "target": {
    "repo": "https://github.com/example/target-go-service.git",
    "base_ref": "638f94be75c448179ecf434e103eecc34c531059",
    "language": "go",
    "package_manager": "go",
    "setup_commands": ["go mod download"],
    "test_commands": ["go test ./..."],
    "working_directory": "."
  }
}
```

Rust:

```json
{
  "target": {
    "repo": "git@gitlab.com:example/target-rust-crate.git",
    "base_ref": "1234567890abcdef1234567890abcdef12345678",
    "language": "rust",
    "package_manager": "cargo",
    "setup_commands": [],
    "test_commands": ["cargo test", "cargo clippy --all-targets -- -D warnings"],
    "working_directory": "."
  }
}
```

## Current Boundary

`prepare_run.py` clones the target repo into an isolated run worktree and checks out `target.base_ref`. `execute_run.py` then runs setup and test commands inside that prepared worktree and records `test.log`, `diff.patch`, and mechanical run facts.

Put the exact commands in `target.test_commands` and mirror them in `tests.sh` when the task needs a single executable entrypoint.
