from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import eval as eval_module


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init_remote_repo(tmp_path: Path) -> tuple[Path, str]:
    source = tmp_path / "source"
    source.mkdir()
    run_git(source, "init", "-b", "main")
    run_git(source, "config", "user.email", "test@example.com")
    run_git(source, "config", "user.name", "Test User")
    (source / "value.txt").write_text("red\n", encoding="utf-8")
    run_git(source, "add", "value.txt")
    run_git(source, "commit", "-m", "test: add red baseline")
    base_ref = run_git(source, "rev-parse", "HEAD")

    remote = tmp_path / "remote.git"
    run_git(tmp_path, "clone", "--bare", str(source), str(remote))
    return remote, base_ref


def write_task(root: Path, repo: Path, base_ref: str) -> None:
    task_dir = root / "benchmarks" / "tasks" / "example-task"
    task_dir.mkdir(parents=True)
    (task_dir / "task.md").write_text("# Task\nEdit value.txt.\n", encoding="utf-8")
    (task_dir / "acceptance.md").write_text("# Acceptance\nvalue.txt exists.\n", encoding="utf-8")
    write_json(
        task_dir / "task.json",
        {
            "id": "example-task",
            "time_budget_minutes": 10,
            "max_human_interventions": 2,
            "max_cost_usd": 1.0,
            "target": {
                "repo": str(repo),
                "base_ref": base_ref,
                "language": "text",
                "package_manager": "",
                "setup_commands": [],
                "test_commands": ["test -f value.txt"],
                "working_directory": ".",
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
        },
    )


def init_eval_root(tmp_path: Path) -> tuple[Path, str]:
    remote, base_ref = init_remote_repo(tmp_path)
    root = tmp_path / "evaluation"
    write_task(root, remote, base_ref)
    return root, base_ref


def manual_review_assignments() -> list[str]:
    return [
        "correctness=1.0",
        "regression_safety=1.0",
        "maintainability=0.8",
        "test_quality=0.8",
        "security=1.0",
        "process_compliance=0.6",
    ]


def test_start_creates_run_and_current_pointer(tmp_path):
    root, _ = init_eval_root(tmp_path)

    metadata = eval_module.start_run(root, "baseline", "example-task", run_id="demo-001", model="gpt-5.5")

    current = json.loads((root / "runs" / ".current.json").read_text(encoding="utf-8"))
    run_dir = root / "runs" / "baseline" / "example-task" / "demo-001"
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert metadata["run_dir"] == "runs/baseline/example-task/demo-001"
    assert current == {
        "workflow_id": "baseline",
        "task_id": "example-task",
        "run_id": "demo-001",
        "run_dir": "runs/baseline/example-task/demo-001",
    }
    assert run["model"] == "gpt-5.5"
    assert (run_dir / "target" / ".git").exists()


def test_target_and_env_use_current_pointer(tmp_path):
    root, _ = init_eval_root(tmp_path)
    eval_module.start_run(root, "baseline", "example-task", run_id="demo-001")

    target = eval_module.target_path(root)
    env = eval_module.shell_env(root)

    assert target == str(root / "runs" / "baseline" / "example-task" / "demo-001" / "target")
    assert f"export AI_EVAL_REPO={root}" in env
    assert f"export AI_EVAL_RUN_DIR={root / 'runs' / 'baseline' / 'example-task' / 'demo-001'}" in env
    assert f"export AI_EVAL_TARGET_WORKTREE={target}" in env
    assert "export AI_EVAL_PHASE=coding" in env


def test_collect_uses_current_pointer(tmp_path):
    root, _ = init_eval_root(tmp_path)
    eval_module.start_run(root, "baseline", "example-task", run_id="demo-001")
    target = Path(eval_module.target_path(root))
    (target / "value.txt").write_text("blue\n", encoding="utf-8")

    result = eval_module.collect_run(root)

    run_dir = root / "runs" / "baseline" / "example-task" / "demo-001"
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert result["tests"]["required_passed"] is True
    assert run["tests"]["required_passed"] is True
    assert run["diff"]["files_changed"] == 1
    assert "blue" in (run_dir / "diff.patch").read_text(encoding="utf-8")
    assert "$ test -f value.txt" in (run_dir / "test.log").read_text(encoding="utf-8")


def test_score_uses_current_pointer_and_writes_score(tmp_path):
    root, _ = init_eval_root(tmp_path)
    eval_module.start_run(root, "baseline", "example-task", run_id="demo-001")
    target = Path(eval_module.target_path(root))
    (target / "value.txt").write_text("blue\n", encoding="utf-8")
    eval_module.collect_run(root)

    score = eval_module.score_manual_run(root, assignments=manual_review_assignments())

    score_path = root / "runs" / "baseline" / "example-task" / "demo-001" / "score.json"
    persisted = json.loads(score_path.read_text(encoding="utf-8"))
    assert score["score"] == 93.0
    assert persisted["score"] == 93.0
    assert persisted["review_sources"]["correctness"] == "manual"


def test_run_dir_override_ignores_current_pointer(tmp_path):
    root, _ = init_eval_root(tmp_path)
    eval_module.start_run(root, "baseline", "example-task", run_id="first")
    first_run_dir = root / "runs" / "baseline" / "example-task" / "first"
    first_target = first_run_dir / "target"
    eval_module.start_run(root, "baseline", "example-task", run_id="second")

    assert eval_module.target_path(root) != str(first_target)
    assert eval_module.target_path(root, first_run_dir) == str(first_target)


def test_missing_current_pointer_has_clear_error(tmp_path):
    root = tmp_path / "evaluation"

    with pytest.raises(FileNotFoundError, match="python scripts/eval.py start"):
        eval_module.target_path(root)


def test_main_prints_clear_error_without_current_pointer(tmp_path, monkeypatch, capsys):
    root = tmp_path / "evaluation"
    monkeypatch.setattr(eval_module, "ROOT", root)

    with pytest.raises(SystemExit) as error:
        eval_module.main(["target"])

    assert error.value.code == 1
    assert "python scripts/eval.py start" in capsys.readouterr().err
