# 多语言目标项目

[英文版](multi-language-targets.md)

这个 benchmark 本身与编程语言无关。每个任务通过目标仓库、固定起始版本、安装命令和测试命令来描述被评估项目。

## 目标元数据

每个 `task.json` 可以包含：

```json
{
  "target": {
    "repo": "https://github.com/owner/repo.git",
    "base_ref": "完整 commit SHA",
    "solution_ref": "可选参考解 commit SHA",
    "language": "typescript",
    "package_manager": "pnpm",
    "setup_commands": ["pnpm install"],
    "test_commands": ["pnpm test", "pnpm lint"],
    "working_directory": "."
  }
}
```

`base_ref` 很关键。没有固定起始版本，两个工作流的运行结果就不是真正可比较的。`benchmarks/tasks/` 下的公开 benchmark 任务必须使用可 clone 的 Git URL 和完整 commit SHA。本地文件路径只用于 `benchmarks/local/` 实验任务和模板。

`solution_ref` 是可选信息字段。它可以指向给 reviewer 参考的参考实现 commit，但不是唯一有效解，也不会被 `prepare_run.py`、`execute_run.py`、`score_run.py` 或报告使用。

## 示例

Python：

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

TypeScript：

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

Go：

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

Rust：

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

## 当前边界

`prepare_run.py` 会把目标仓库 clone 到隔离的 run worktree，并 checkout 到 `target.base_ref`。`execute_run.py` 随后在这个准备好的 worktree 内执行 setup/test 命令，并记录 `test.log`、`diff.patch` 和机械 run 事实。

请把精确命令写入 `target.test_commands`。如果任务需要单一可执行入口，也把同样的命令同步到 `tests.sh`。
