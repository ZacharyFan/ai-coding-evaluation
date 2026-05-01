import json
from pathlib import Path

import pytest

from scripts.validate_task import expand_task_dirs, validate_task_dir


FULL_SHA = "638f94be75c448179ecf434e103eecc34c531059"


@pytest.mark.parametrize("template", ["bugfix", "feature", "refactor", "test", "frontend"])
def test_task_type_templates_are_valid(template):
    errors = validate_task_dir(Path("benchmarks/templates") / template)

    assert errors == []


def test_default_task_root_discovers_real_tasks_only():
    task_dirs = expand_task_dirs([Path("benchmarks/tasks")])

    assert Path("benchmarks/tasks/go-bugfix-001") in task_dirs
    assert all("templates" not in task_dir.parts for task_dir in task_dirs)


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
  "scoring_weights": {
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
    task_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("# Task\n", encoding="utf-8")
    (task_dir / "acceptance.md").write_text("# Acceptance\n", encoding="utf-8")
    tests_sh = task_dir / "tests.sh"
    tests_sh.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    tests_sh.chmod(0o755)
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
            "base_ref": FULL_SHA,
            "language": "go",
            "test_commands": ["./tests.sh"],
        },
        "scoring_weights": {
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


def test_legacy_scoring_is_invalid(tmp_path):
    task_dir = tmp_path / "task"
    task = json.loads(valid_task_json())
    task["scoring"] = task.pop("scoring_weights")
    write_task(task_dir, json.dumps(task, indent=2))

    errors = validate_task_dir(task_dir)

    assert any("obsolete keys: scoring" in error for error in errors)
    assert any("missing keys: scoring_weights" in error for error in errors)


def test_missing_scoring_weights_is_invalid(tmp_path):
    task_dir = tmp_path / "task"
    task = json.loads(valid_task_json())
    del task["scoring_weights"]
    write_task(task_dir, json.dumps(task, indent=2))

    errors = validate_task_dir(task_dir)

    assert any("missing keys: scoring_weights" in error for error in errors)


def test_missing_scoring_weights_dimension_is_invalid(tmp_path):
    task_dir = tmp_path / "task"
    task = json.loads(valid_task_json())
    del task["scoring_weights"]["security"]
    write_task(task_dir, json.dumps(task, indent=2))

    errors = validate_task_dir(task_dir)

    assert any("missing scoring_weights keys: security" in error for error in errors)


def test_scoring_weights_must_sum_to_100(tmp_path):
    task_dir = tmp_path / "task"
    task = json.loads(valid_task_json())
    task["scoring_weights"]["efficiency"] = 9
    write_task(task_dir, json.dumps(task, indent=2))

    errors = validate_task_dir(task_dir)

    assert any("scoring_weights must sum to 100, got 99" in error for error in errors)


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


@pytest.mark.parametrize("filename", ["task.md", "acceptance.md", "tests.sh"])
def test_missing_required_task_files_are_invalid(tmp_path, filename):
    task_dir = tmp_path / "task"
    write_task(task_dir, valid_task_json())
    (task_dir / filename).unlink()

    errors = validate_task_dir(task_dir)

    assert any(f"missing {task_dir / filename}" in error for error in errors)


def test_tests_sh_must_be_executable(tmp_path):
    task_dir = tmp_path / "task"
    write_task(task_dir, valid_task_json())
    (task_dir / "tests.sh").chmod(0o644)

    errors = validate_task_dir(task_dir)

    assert any("tests.sh must be executable" in error for error in errors)


def test_official_task_rejects_local_target_repo(tmp_path):
    root = tmp_path / "benchmarks" / "tasks"
    task_dir = root / "task"
    write_task(task_dir, valid_task_json())

    errors = validate_task_dir(task_dir)

    assert any("official tasks must use a cloneable Git URL" in error for error in errors)


@pytest.mark.parametrize(
    "repo",
    [
        "https://github.com/owner/repo.git",
        "https://gitlab.com/group/project.git",
        "git@github.com:owner/repo.git",
        "git@gitlab.com:group/project.git",
    ],
)
def test_official_task_accepts_remote_git_url_with_full_sha(tmp_path, repo):
    root = tmp_path / "benchmarks" / "tasks"
    task_dir = root / "task"
    write_task(task_dir, valid_task_json(target={"repo": repo, "base_ref": FULL_SHA, "language": "go", "test_commands": ["./tests.sh"]}))

    errors = validate_task_dir(task_dir)

    assert errors == []


@pytest.mark.parametrize("base_ref", ["main", "master", "v1.2.3", "abc123"])
def test_official_task_rejects_floating_or_short_base_ref(tmp_path, base_ref):
    root = tmp_path / "benchmarks" / "tasks"
    task_dir = root / "task"
    write_task(
        task_dir,
        valid_task_json(
            target={
                "repo": "https://github.com/owner/repo.git",
                "base_ref": base_ref,
                "language": "go",
                "test_commands": ["./tests.sh"],
            }
        ),
    )

    errors = validate_task_dir(task_dir)

    assert any("official tasks must pin target.base_ref to a full commit SHA" in error for error in errors)


def test_local_task_allows_local_target_repo(tmp_path):
    root = tmp_path / "benchmarks" / "local"
    task_dir = root / "task"
    write_task(task_dir, valid_task_json())

    errors = validate_task_dir(task_dir)

    assert errors == []
