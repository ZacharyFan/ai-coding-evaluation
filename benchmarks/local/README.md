# Local Benchmark Tasks

[Chinese version](README.zh-CN.md)

Use this directory for private or local experiment tasks that should not become part of the public benchmark set.

Files under `benchmarks/local/` are ignored by git by default. They can use local filesystem paths in `target.repo`, but they do not participate in default reports and are not suitable for external contribution PRs.

Public, reusable tasks belong in `benchmarks/tasks/` and must use a cloneable Git URL plus a fixed full commit SHA.
