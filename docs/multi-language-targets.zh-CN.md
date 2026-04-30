# 多语言目标项目

[英文版](multi-language-targets.md)

这个 benchmark 本身与编程语言无关。每个任务通过目标仓库、固定起始版本、安装命令和测试命令来描述被评估项目。

## 目标元数据

每个 `task.json` 可以包含：

```json
{
  "target": {
    "repo": "owner/name、远程 URL 或本地路径",
    "base_ref": "commit-sha-or-tag",
    "language": "typescript",
    "package_manager": "pnpm",
    "setup_commands": ["pnpm install"],
    "test_commands": ["pnpm test", "pnpm lint"],
    "working_directory": "."
  }
}
```

`base_ref` 很关键。没有固定起始版本，两个工作流的运行结果就不是真正可比较的。

## 示例

Python：

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

TypeScript：

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

Go：

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

Rust：

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

## 当前边界

本仓库负责记录和评分 run。目前还不会自动 clone 仓库、安装依赖或执行目标项目测试。

现阶段请把精确命令写入 `target.test_commands`。如果任务需要单一可执行入口，也把同样的命令同步到 `tests.sh`。

