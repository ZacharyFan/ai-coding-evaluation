from pathlib import Path

from scripts.validate_task import validate_task_dir


def test_sample_task_is_valid():
    errors = validate_task_dir(Path("benchmarks/tasks/bugfix-001"))

    assert errors == []


def test_target_metadata_is_validated(tmp_path):
    task_dir = tmp_path / "bad-task"
    task_dir.mkdir()
    (task_dir / "task.md").write_text("# Task\n", encoding="utf-8")
    (task_dir / "acceptance.md").write_text("# Acceptance\n", encoding="utf-8")
    (task_dir / "tests.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (task_dir / "task.json").write_text(
        """
{
  "id": "bad-task",
  "type": "bugfix",
  "effort_size": "small",
  "complexity": {
    "business_complexity": "L1_standardized",
    "context_maturity": "C1_complete"
  },
  "time_budget_minutes": 10,
  "required_tests": ["./tests.sh"],
  "hidden_checks": [],
  "target": {
    "repo": "../repo",
    "base_ref": "abc123",
    "language": "go",
    "test_commands": []
  },
  "scoring": {
    "correctness": 35,
    "regression_safety": 15,
    "maintainability": 15,
    "test_quality": 10,
    "security": 10,
    "process_compliance": 5,
    "efficiency": 10
  }
}
""",
        encoding="utf-8",
    )

    errors = validate_task_dir(task_dir)

    assert any("target.test_commands must be a non-empty list" in error for error in errors)


def write_task(task_dir, task_json):
    task_dir.mkdir()
    (task_dir / "task.md").write_text("# Task\n", encoding="utf-8")
    (task_dir / "acceptance.md").write_text("# Acceptance\n", encoding="utf-8")
    (task_dir / "tests.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (task_dir / "task.json").write_text(task_json, encoding="utf-8")


def valid_task_json(**overrides):
    task = {
        "id": "task",
        "type": "bugfix",
        "effort_size": "small",
        "complexity": {
            "business_complexity": "L1_standardized",
            "context_maturity": "C1_complete",
        },
        "time_budget_minutes": 10,
        "required_tests": ["./tests.sh"],
        "hidden_checks": [],
        "target": {
            "repo": "../repo",
            "base_ref": "abc123",
            "language": "go",
            "test_commands": ["./tests.sh"],
        },
        "scoring": {
            "correctness": 35,
            "regression_safety": 15,
            "maintainability": 15,
            "test_quality": 10,
            "security": 10,
            "process_compliance": 5,
            "efficiency": 10,
        },
    }
    task.update(overrides)
    import json

    return json.dumps(task, indent=2)


def test_missing_effort_size_is_invalid(tmp_path):
    task_dir = tmp_path / "task"
    task = valid_task_json()
    task = task.replace('  "effort_size": "small",\n', "")
    write_task(task_dir, task)

    errors = validate_task_dir(task_dir)

    assert any("missing keys: effort_size" in error for error in errors)


def test_legacy_difficulty_is_invalid(tmp_path):
    task_dir = tmp_path / "task"
    task = valid_task_json(difficulty="small")
    write_task(task_dir, task)

    errors = validate_task_dir(task_dir)

    assert any("obsolete keys: difficulty" in error for error in errors)


def test_invalid_complexity_values_are_invalid(tmp_path):
    task_dir = tmp_path / "task"
    task = valid_task_json(
        complexity={
            "business_complexity": "L4_magic",
            "context_maturity": "C4_mystery",
        }
    )
    write_task(task_dir, task)

    errors = validate_task_dir(task_dir)

    assert any("complexity.business_complexity must be one of" in error for error in errors)
    assert any("complexity.context_maturity must be one of" in error for error in errors)
