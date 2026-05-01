from pathlib import Path

from scripts.execute_run import load_json


EXAMPLE_ROOT = Path("examples/go-bugfix-001")


def test_go_bugfix_example_task_is_valid():
    task_dir = EXAMPLE_ROOT / "task"
    task = load_json(task_dir / "task.json")

    assert task["id"] == "go-bugfix-001"
    assert task["target"]["repo"] == "https://github.com/ZacharyFan/ai-coding-evaluation-demo-golang.git"
    for filename in (
        "task.md",
        "task.zh-CN.md",
        "acceptance.md",
        "acceptance.zh-CN.md",
        "tests.sh",
    ):
        assert (task_dir / filename).exists()


def test_go_bugfix_example_run_and_score_are_valid_json():
    run = load_json(EXAMPLE_ROOT / "run" / "run.json")
    score = load_json(EXAMPLE_ROOT / "run" / "score.json")

    assert run["workflow_id"] == "baseline"
    assert run["task_id"] == "go-bugfix-001"
    assert "review" not in run
    assert "score" not in run
    assert score["workflow_id"] == "baseline"
    assert score["task_id"] == "go-bugfix-001"
    assert score["score"] == 100.0


def test_go_bugfix_example_has_bilingual_narrative_files():
    for path in (
        EXAMPLE_ROOT / "README.md",
        EXAMPLE_ROOT / "README.zh-CN.md",
        EXAMPLE_ROOT / "run" / "transcript.md",
        EXAMPLE_ROOT / "run" / "transcript.zh-CN.md",
    ):
        assert path.exists()


def test_go_bugfix_example_does_not_use_standard_review_markdown():
    assert not (EXAMPLE_ROOT / "run" / "review.md").exists()
    assert not (EXAMPLE_ROOT / "run" / "review.zh-CN.md").exists()
