# 本地评估任务

[English](README.md)

这个目录用于放私有或本地实验任务，不属于公开 benchmark 集合。

`benchmarks/local/` 下的文件默认被 git 忽略。这里的任务可以在 `target.repo` 中使用本地文件路径，但不会进入默认报告，也不适合作为外部贡献 PR。

公开、可复跑的任务应放在 `benchmarks/tasks/`，并且必须使用可 clone 的 Git URL 和固定的完整 commit SHA。
