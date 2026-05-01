from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.prepare_run import prepare_run


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
    write_json(
        task_dir / "task.json",
        {
            "id": "example-task",
            "target": {
                "repo": str(repo),
                "base_ref": base_ref,
                "language": "text",
                "package_manager": "",
                "setup_commands": [],
                "test_commands": ["test -f value.txt"],
                "working_directory": ".",
            },
        },
    )


def test_prepare_run_clones_target_and_writes_run_json(tmp_path):
    remote, base_ref = init_remote_repo(tmp_path)
    root = tmp_path / "evaluation"
    write_task(root, remote, base_ref)

    run_dir = prepare_run(root, "baseline", "example-task", "demo-001")

    target = run_dir / "target"
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    assert (target / ".git").exists()
    assert (target / "value.txt").read_text(encoding="utf-8") == "red\n"
    assert run_git(target, "rev-parse", "HEAD") == base_ref
    assert run_dir == root / "runs" / "baseline" / "example-task" / "demo-001"
    assert run["workflow_id"] == "baseline"
    assert not (run_dir / "metrics.json").exists()
    assert run["target"]["repo"] == str(remote)
    assert run["target"]["base_ref"] == base_ref
    assert run["target"]["worktree"] == str(target)
    assert run["tests"]["hidden_passed"] is None
    assert run["process_evidence"]["self_review_performed"] is False
    assert "review" not in run
    assert "score" not in run
    assert not (run_dir / "review.md").exists()


def test_prepare_run_fails_when_run_directory_exists(tmp_path):
    remote, base_ref = init_remote_repo(tmp_path)
    root = tmp_path / "evaluation"
    write_task(root, remote, base_ref)
    run_dir = root / "runs" / "baseline" / "example-task" / "demo-001"
    run_dir.mkdir(parents=True)

    with pytest.raises(FileExistsError, match="run directory already exists"):
        prepare_run(root, "baseline", "example-task", "demo-001")


@pytest.mark.parametrize("workflow_id", ["", "../x", "a/b", "bad id", "..", "a..b"])
def test_prepare_run_rejects_unsafe_workflow_ids(tmp_path, workflow_id):
    root = tmp_path / "evaluation"

    with pytest.raises(ValueError, match="workflow_id"):
        prepare_run(root, workflow_id, "example-task", "demo-001")
