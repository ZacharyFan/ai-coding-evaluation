from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.benchmark_registry import page_html, write_registry


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_task(root: Path, task_id: str = "python-feature-l1-c1") -> Path:
    task_dir = root / "benchmarks" / "tasks" / task_id
    task_dir.mkdir(parents=True)
    write_json(
        task_dir / "task.json",
        {
            "id": task_id,
            "type": "feature",
            "effort_size": "small",
            "complexity": {
                "business_complexity": "L1_standardized",
                "context_maturity": "C1_complete",
            },
            "time_budget_minutes": 20,
            "max_human_interventions": 1,
            "max_cost_usd": 0.5,
            "hidden_checks": ["No hardcoded visible test special-case."],
            "context_sources": [{"type": "project_doc", "path_globs": ["README.md"]}],
            "scope": {"allowed_paths": ["src/**", "tests/**", "README.md", "pyproject.toml"]},
            "target": {
                "language": "python",
                "package_manager": "pip",
                "test_commands": ["pytest tests/test_feature.py"],
            },
        },
    )
    (task_dir / "task.md").write_text(
        "\n".join(
            [
                "# Task: Add import preview",
                "",
                "Scenario: data import (`importer`).",
                "",
                "Expected behavior:",
                "",
                "- preview returns parsed rows",
                "- invalid input returns an error",
            ]
        ),
        encoding="utf-8",
    )
    (task_dir / "task.zh-CN.md").write_text(
        "\n".join(
            [
                "# 任务：新增导入预览",
                "",
                "场景：数据导入（importer）。",
                "",
                "期望行为：",
                "",
                "- preview 返回解析后的行",
                "- 非法输入返回 error",
            ]
        ),
        encoding="utf-8",
    )
    return task_dir


def script_tasks(html: str) -> list[dict]:
    match = re.search(r"const TASKS = (\[[\s\S]*?\]);\n    const labels", html)
    assert match
    return json.loads(match.group(1))


def test_write_registry_generates_language_agnostic_bilingual_pages(tmp_path):
    write_task(tmp_path)

    output, zh_output = write_registry(
        tmp_path / "benchmarks" / "tasks",
        tmp_path / "benchmarks" / "index.html",
    )

    html = output.read_text(encoding="utf-8")
    zh_html = zh_output.read_text(encoding="utf-8")
    assert "Go task matrix" not in html
    assert "公开 Go" not in zh_html
    assert "A static registry for public benchmark tasks" in html
    assert "公开测评任务矩阵" in zh_html
    assert "index.zh-CN.html" in html
    assert 'index.html">English' in zh_html
    assert "white-space: nowrap" in zh_html


def test_registry_uses_localized_task_markdown_and_links(tmp_path):
    write_task(tmp_path)

    _, zh_output = write_registry(
        tmp_path / "benchmarks" / "tasks",
        tmp_path / "benchmarks" / "index.html",
    )

    tasks = script_tasks(zh_output.read_text(encoding="utf-8"))
    assert tasks == [
        {
            "b": "L1_standardized",
            "c": "C1_complete",
            "cmd": "pytest tests/test_feature.py",
            "contexts": 1,
            "cost": 0.5,
            "effort": "small",
            "hidden": 1,
            "id": "python-feature-l1-c1",
            "interventions": 1,
            "jsonHref": "tasks/python-feature-l1-c1/task.json",
            "minutes": 20,
            "scenario": "数据导入（importer）",
            "scope": ["src/**", "tests/**", "README.md"],
            "scopeMore": 1,
            "summary": "preview 返回解析后的行；非法输入返回 error",
            "taskHref": "tasks/python-feature-l1-c1/task.zh-CN.md",
            "testsHref": "tasks/python-feature-l1-c1/tests.sh",
            "title": "新增导入预览",
            "type": "feature",
        }
    ]


def test_page_html_keeps_chinese_title_on_one_line():
    html = page_html([], "zh-CN")

    assert '<body class="locale-zh">' in html
    assert "可执行 Benchmark 任务，一屏掌握。" in html
    assert ".locale-zh h1" in html
    assert "white-space: nowrap" in html


def test_page_html_keeps_task_cards_visually_aligned():
    html = page_html([], "en")

    assert "grid-auto-rows: 1fr" in html
    assert ".task-title" in html
    assert "-webkit-line-clamp: 2" in html
    assert "-webkit-line-clamp: 3" in html
    assert "height: 60px" in html
    assert "height: 54px" in html
