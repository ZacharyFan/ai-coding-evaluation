# Multi-Language Targets

[Chinese version](multi-language-targets.zh-CN.md)

The benchmark is language-agnostic. A task describes the target repo, fixed base revision, setup commands, and test commands.

## Target Metadata

Each `task.json` can include:

```json
{
  "target": {
    "repo": "owner/name, remote URL, or local path",
    "base_ref": "commit-sha-or-tag",
    "language": "typescript",
    "package_manager": "pnpm",
    "setup_commands": ["pnpm install"],
    "test_commands": ["pnpm test", "pnpm lint"],
    "working_directory": "."
  }
}
```

`base_ref` matters. Without a fixed starting revision, two workflow runs are not really comparable.

## Examples

Python:

```json
{
  "target": {
    "repo": "../target-python-app",
    "base_ref": "9f3c2a1",
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
    "repo": "../target-web-app",
    "base_ref": "4b8d10c",
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
    "repo": "../target-go-service",
    "base_ref": "v1.2.3",
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
    "repo": "../target-rust-crate",
    "base_ref": "main",
    "language": "rust",
    "package_manager": "cargo",
    "setup_commands": [],
    "test_commands": ["cargo test", "cargo clippy --all-targets -- -D warnings"],
    "working_directory": "."
  }
}
```

## Current Boundary

This repository records and scores runs. It does not yet clone repos, install dependencies, or execute target tests automatically.

For now, put the exact commands in `target.test_commands` and mirror them in `tests.sh` when the task needs a single executable entrypoint.

