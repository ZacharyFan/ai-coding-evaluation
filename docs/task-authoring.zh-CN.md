# 评估用例编写指南

[英文版](task-authoring.md)

评估用例是一个受控实验。目标不是证明某个 AI “看起来会写代码”，而是判断哪个 AI Coding workflow 能在可复跑条件下产出可接受变更。

## 好用例的标准

好用例有五个性质：

- 真实：来自真实代码库，或足够忠实地抽取自真实任务
- 固定：绑定可 clone 的目标仓库和完整 commit SHA
- 可观察：可以通过测试、review 或二者判断成败
- 有边界：预期 diff 足够收敛，能被 review
- 公平：每个 workflow 拿到相同说明和相同起点

弱用例通常会破坏其中一条。最常见的问题是任务太虚，只能靠审美判断。

## 需要编写的文件

从 `benchmarks/templates/` 中最接近的类型模板复制开始。公开、可复用任务放到 `benchmarks/tasks/<task-id>`。私有或本地实验任务放到 `benchmarks/local/<task-id>`。

`task.md` 是任务提示词，也是 AI Coding workflow 的标准输入物。按 workflow 应该看到的方式编写，包含问题、预期行为、复现步骤和已知约束。不要写 hidden solution 或 reviewer 专用参考答案。

`acceptance.md` 是 blind review 阶段的参考答案。Reviewer 应该能在不知道产出 workflow 的前提下判断最终 diff 是否可接受。它可以比 `task.md` 更明确，但仍应描述可接受行为，而不是规定唯一实现路径。

`tests.sh` 是必跑检查入口。它必须可执行、确定性强。优先写能在任务解决前失败的检查；如果缺陷不适合用短脚本复现，也可以写回归保护检查。

`task.json` 是任务契约。它描述目标仓库、预算、复杂度、必跑测试、hidden checks 和 `scoring_weights`。公开任务必须在 `target.repo` 中使用标准 Git clone URL，并在 `target.base_ref` 中使用完整 commit SHA；本地文件路径只用于 `benchmarks/local/`。

## 如何选择规模和复杂度

用 `effort_size` 表达工作量：

```text
small    局部改动，通常是一个行为或一个窄测试缺口
medium   涉及多个文件、需要调查，或是中等功能/重构
large    范围较宽的实现、迁移，或多个关联改动
```

用 `business_complexity` 表达推理难度：

```text
L1_standardized  标准模式、简单状态、任务到代码映射直接
L2_linked        多状态、字段联动、集成、多步骤行为
L3_complex       定制架构、深层 UI/状态行为、复杂数据流
```

用 `context_maturity` 表达 agent 是否有足够项目知识：

```text
C1_complete      相关文档、示例、API 和约定可找到
C2_partial       有部分上下文，但分散、过时或不完整
C3_missing       agent 必须推断重要上下文或补齐缺失结构
```

这些维度刻意拆开。依赖升级可能工作量大但复杂度低；一行鉴权条件可能工作量小但复杂度高。

## 如何写 Hidden Checks

Hidden checks 应该防止投机解法，而不是泄露答案。

好例子：

```text
The fix is implemented at the source of the behavior, not by special-casing the visible test.
No public API behavior changes beyond the requested behavior.
The solution handles empty and multi-item inputs.
```

弱例子：

```text
Change function parseUserInput in src/parser.ts.
Use exactly this SQL query.
Make it better.
```

## 反模式

出现这些情况就应该拒绝或重写：

- 没有固定 `base_ref`
- `benchmarks/tasks/` 使用只在本机存在的 target repo 路径
- 依赖 agent 看不到的私有上下文
- 验收标准完全依赖主观审美
- 测试无论实现如何都会通过
- 任务需要生产凭据或真实客户数据
- 把巨大迁移伪装成 `small`
- hidden checks 规定解法路径，而不是规定目标行为

## 本地验证

开 PR 前运行：

```bash
python scripts/validate_task.py benchmarks/tasks/<task-id>
pytest
```

第一个命令验证任务贡献本身。第二个命令保护 benchmark 工具链。

显式校验模板：

```bash
python scripts/validate_task.py benchmarks/templates
```

显式校验本地实验任务：

```bash
python scripts/validate_task.py benchmarks/local
```
