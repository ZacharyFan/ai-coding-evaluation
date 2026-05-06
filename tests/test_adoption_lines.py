from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import adoption_lines


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "target"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")
    (repo / "value.txt").write_text("base\n", encoding="utf-8")
    run_git(repo, "add", "value.txt")
    run_git(repo, "commit", "-m", "test: base")
    return repo, run_git(repo, "rev-parse", "HEAD")


def commit_all(repo: Path, message: str) -> str:
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-m", message)
    return run_git(repo, "rev-parse", "HEAD")


def write_run(root: Path, repo: Path, base_ref: str, *, adoption: dict | None = None) -> Path:
    run_path = root / "runs" / "baseline" / "example-task" / "demo" / "run.json"
    write_json(
        run_path,
        {
            "workflow_id": "baseline",
            "task_id": "example-task",
            "target": {
                "base_ref": base_ref,
                "worktree": str(repo),
            },
            "duration_minutes": 1,
            "human_interventions": 0,
            "tests": {"required_passed": True, "hidden_passed": None},
            "diff": {"files_changed": 1, "unrelated_files_changed": 0},
            "adoption": adoption
            or {
                "candidate_ref": None,
                "accepted_ref": None,
                "ai_generated_lines": None,
                "accepted_lines": None,
                "adoption_rate": None,
            },
        },
    )
    return run_path


def test_adoption_lines_requires_candidate_and_accepted_refs(tmp_path):
    repo, base_ref = init_repo(tmp_path)
    root = tmp_path / "evaluation"
    run_path = write_run(root, repo, base_ref)

    with pytest.raises(ValueError, match="Fill run.json.adoption.candidate_ref and accepted_ref"):
        adoption_lines.calculate_adoption(run_path)


def test_adoption_lines_resolves_refs_and_counts_kept_lines(tmp_path):
    repo, base_ref = init_repo(tmp_path)
    root = tmp_path / "evaluation"
    (repo / "value.txt").write_text("base\nalpha\nbeta\nbeta\ngamma\n", encoding="utf-8")
    candidate_ref = commit_all(repo, "test: candidate")
    run_git(repo, "checkout", "-b", "accepted", base_ref)
    (repo / "value.txt").write_text("base\nalpha\nbeta\ngamma\n", encoding="utf-8")
    accepted_ref = commit_all(repo, "test: accepted")
    run_path = write_run(root, repo, base_ref)

    result = adoption_lines.calculate_adoption(
        run_path,
        candidate_ref=candidate_ref[:8],
        accepted_ref="accepted",
        write=True,
    )

    updated = json.loads(run_path.read_text(encoding="utf-8"))
    assert result["adoption"]["candidate_ref"] == candidate_ref
    assert result["adoption"]["accepted_ref"] == accepted_ref
    assert result["adoption"]["ai_generated_lines"] == 4
    assert result["adoption"]["accepted_lines"] == 3
    assert result["adoption"]["adoption_rate"] == 0.75
    assert updated["adoption"] == result["adoption"]


def test_adoption_lines_does_not_count_rewritten_candidate_lines(tmp_path):
    repo, base_ref = init_repo(tmp_path)
    root = tmp_path / "evaluation"
    (repo / "value.txt").write_text("base\nalpha\nbeta\n", encoding="utf-8")
    candidate_ref = commit_all(repo, "test: candidate")
    run_git(repo, "checkout", "-b", "accepted", base_ref)
    (repo / "value.txt").write_text("base\nalpha\nbeta changed\n", encoding="utf-8")
    accepted_ref = commit_all(repo, "test: accepted")
    run_path = write_run(root, repo, base_ref)

    result = adoption_lines.calculate_adoption(
        run_path,
        candidate_ref=candidate_ref,
        accepted_ref=accepted_ref,
    )

    assert result["adoption"]["ai_generated_lines"] == 2
    assert result["adoption"]["accepted_lines"] == 1
    assert result["adoption"]["adoption_rate"] == 0.5


def test_adoption_lines_respects_task_scope_allowlist(tmp_path):
    repo, base_ref = init_repo(tmp_path)
    root = tmp_path / "evaluation"
    task_dir = root / "benchmarks" / "tasks" / "example-task"
    write_json(task_dir / "task.json", {"id": "example-task", "scope": {"allowed_paths": ["value.txt"]}})
    (repo / "value.txt").write_text("base\nkept\n", encoding="utf-8")
    (repo / "notes.md").write_text("scope out\n", encoding="utf-8")
    candidate_ref = commit_all(repo, "test: candidate")
    run_git(repo, "checkout", "-b", "accepted", base_ref)
    (repo / "value.txt").write_text("base\nkept\n", encoding="utf-8")
    (repo / "notes.md").write_text("scope out\n", encoding="utf-8")
    accepted_ref = commit_all(repo, "test: accepted")
    run_path = write_run(root, repo, base_ref)

    result = adoption_lines.calculate_adoption(
        run_path,
        candidate_ref=candidate_ref,
        accepted_ref=accepted_ref,
    )

    assert result["adoption"]["ai_generated_lines"] == 1
    assert result["adoption"]["accepted_lines"] == 1
    assert result["adoption"]["adoption_rate"] == 1.0


def test_adoption_lines_sets_rate_to_null_when_candidate_added_no_lines(tmp_path):
    repo, base_ref = init_repo(tmp_path)
    root = tmp_path / "evaluation"
    candidate_ref = base_ref
    accepted_ref = base_ref
    run_path = write_run(root, repo, base_ref)

    result = adoption_lines.calculate_adoption(
        run_path,
        candidate_ref=candidate_ref,
        accepted_ref=accepted_ref,
    )

    assert result["adoption"]["ai_generated_lines"] == 0
    assert result["adoption"]["accepted_lines"] == 0
    assert result["adoption"]["adoption_rate"] is None
