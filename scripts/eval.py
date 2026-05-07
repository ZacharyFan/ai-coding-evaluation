#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from scripts import dashboard as dashboard_module
from scripts import llm_review_run as llm_review_module
from scripts import report as report_module
from scripts import score_run as score_module
from scripts.adoption_lines import calculate_adoption
from scripts.collect_run import collect_run as collect_run_evidence
from scripts.prepare_run import prepare_run
from scripts.show_solution_diff import show_solution_diff


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def current_path(root: Path) -> Path:
    return root / "runs" / ".current.json"


def looks_like_eval_repo(path: Path) -> bool:
    return (path / "benchmarks" / "tasks").exists()


def looks_like_current_eval_repo(path: Path) -> bool:
    return looks_like_eval_repo(path) and current_path(path).exists()


def find_repo_from_cwd(cwd: Path) -> Path | None:
    for candidate in [cwd.resolve(), *cwd.resolve().parents]:
        if looks_like_current_eval_repo(candidate):
            return candidate
    return None


def resolve_root(repo_arg: Path | None = None) -> Path:
    candidates: list[Path] = []
    if repo_arg:
        candidates.append(repo_arg)
    env_repo = os.environ.get("AI_EVAL_REPO")
    if env_repo:
        candidates.append(Path(env_repo))
    candidates.append(SCRIPT_ROOT)
    cwd_repo = find_repo_from_cwd(Path.cwd())
    if cwd_repo:
        candidates.append(cwd_repo)

    for candidate in candidates:
        root = candidate.expanduser().resolve()
        if looks_like_eval_repo(root):
            return root

    raise FileNotFoundError(
        "evaluation repo not found. Pass --repo /path/to/ai-coding-evaluation or set AI_EVAL_REPO."
    )


def path_for_display(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def resolve_repo_path(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return root / path


def run_dir_from_current(root: Path) -> Path:
    path = current_path(root)
    if not path.exists():
        raise FileNotFoundError(
            "no current run found. Run `python scripts/eval.py start --workflow <workflow> --task <task-id>` first, "
            "or pass --repo /path/to/ai-coding-evaluation and --run-dir runs/<workflow>/<task-id>/<run-id>."
        )
    current = load_json(path)
    run_dir = current.get("run_dir")
    if not isinstance(run_dir, str) or not run_dir:
        raise ValueError(f"invalid current run pointer: {path}")
    return resolve_repo_path(root, Path(run_dir))


def resolve_run_dir(root: Path, run_dir: Path | None = None) -> Path:
    resolved = resolve_repo_path(root, run_dir) if run_dir else run_dir_from_current(root)
    if not (resolved / "run.json").exists():
        raise FileNotFoundError(f"run.json not found in run directory: {resolved}")
    return resolved


def task_path_for_run(root: Path, run_dir: Path) -> Path:
    run = load_json(run_dir / "run.json")
    task_id = run.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError(f"run.json is missing task_id: {run_dir / 'run.json'}")
    task_path = root / "benchmarks" / "tasks" / task_id / "task.json"
    if not task_path.exists():
        raise FileNotFoundError(f"task.json not found for current run: {task_path}")
    return task_path


def current_metadata(root: Path, run_dir: Path) -> dict[str, Any]:
    run = load_json(run_dir / "run.json")
    return {
        "workflow_id": run.get("workflow_id", ""),
        "task_id": run.get("task_id", ""),
        "run_id": run_dir.name,
        "run_dir": path_for_display(root, run_dir),
    }


def write_current(root: Path, run_dir: Path) -> dict[str, Any]:
    metadata = current_metadata(root, run_dir)
    write_json(current_path(root), metadata)
    return metadata


def start_run(
    root: Path,
    workflow: str,
    task: str,
    *,
    run_id: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    run_dir = prepare_run(root, workflow, task, run_id, model)
    metadata = write_current(root, run_dir)
    metadata["target"] = str(load_json(run_dir / "run.json")["target"]["worktree"])
    metadata["task_prompt"] = str(run_dir / "task.md")
    if (run_dir / "task.zh-CN.md").exists():
        metadata["task_prompt_zh_CN"] = str(run_dir / "task.zh-CN.md")
    return metadata


def target_path(root: Path, run_dir: Path | None = None) -> str:
    resolved = resolve_run_dir(root, run_dir)
    run = load_json(resolved / "run.json")
    worktree = run.get("target", {}).get("worktree")
    if not isinstance(worktree, str) or not worktree:
        raise ValueError(f"run.target.worktree is missing: {resolved / 'run.json'}")
    return str(resolve_repo_path(root, Path(worktree)))


def shell_env(root: Path, run_dir: Path | None = None) -> str:
    resolved = resolve_run_dir(root, run_dir)
    target = target_path(root, resolved)
    values = {
        "AI_EVAL_REPO": str(root.resolve()),
        "AI_EVAL_RUN_DIR": str(resolved.resolve()),
        "AI_EVAL_TARGET_WORKTREE": str(Path(target).resolve()),
        "AI_EVAL_PHASE": "coding",
    }
    return "\n".join(f"export {key}={shlex.quote(value)}" for key, value in values.items()) + "\n"


def collect_run(root: Path, run_dir: Path | None = None, *, reset_to_base: bool = False, expect_fail: bool = False) -> dict[str, Any]:
    resolved = resolve_run_dir(root, run_dir)
    result = collect_run_evidence(
        task_path_for_run(root, resolved),
        resolved / "run.json",
        write=True,
        reset_to_base=reset_to_base,
        expect_fail=expect_fail,
    )
    if not expect_fail and result.get("tests", {}).get("required_passed") is False:
        raise RuntimeError("required tests failed; inspect test.log before scoring")
    return result


def score_manual_run(
    root: Path,
    run_dir: Path | None = None,
    *,
    assignments: list[str] | None = None,
    manual_hard_gates: list[str] | None = None,
    init: bool = False,
) -> dict[str, Any]:
    resolved = resolve_run_dir(root, run_dir)
    run_path = resolved / "run.json"
    score_path = resolved / "score.json"
    run = load_json(run_path)

    if init:
        return score_module.write_initialized_score(score_path, run)

    task = load_json(task_path_for_run(root, resolved))
    score = load_json(score_path) if score_path.exists() else score_module.init_score_doc(run)
    if assignments or manual_hard_gates is not None:
        score = score_module.apply_manual_review(score, assignments or [], manual_hard_gates)
    result = score_module.score_run(task, run, score)
    score.update(result)
    score_module.write_json(score_path, score)
    return score


def llm_review_shortcut(
    root: Path,
    run_dir: Path | None = None,
    *,
    score_file: Path | None = None,
    base_url: str,
    model: str | None,
    api_key_env: str,
    response_mode: str,
    max_input_chars: int,
    max_tokens: int,
) -> dict[str, Any]:
    if not model:
        raise ValueError("--model or AI_EVAL_REVIEW_MODEL is required")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(f"missing API key env var: {api_key_env}")
    resolved = resolve_run_dir(root, run_dir)
    output_path = resolve_repo_path(root, score_file) if score_file else resolved / "score.json"
    return llm_review_module.llm_review_run(
        task_path_for_run(root, resolved),
        resolved / "run.json",
        output_path,
        write=True,
        base_url=base_url,
        model=model,
        api_key=api_key,
        response_mode=response_mode,
        max_input_chars=max_input_chars,
        max_tokens=max_tokens,
    )


def solution_diff(root: Path, run_dir: Path | None = None, *, color: str = "auto") -> str:
    resolved = resolve_run_dir(root, run_dir)
    return show_solution_diff(task_path_for_run(root, resolved), resolved / "run.json", color=color)


def adoption_run(
    root: Path,
    run_dir: Path | None = None,
    *,
    candidate_ref: str | None = None,
    accepted_ref: str | None = None,
) -> dict[str, Any]:
    resolved = resolve_run_dir(root, run_dir)
    result = calculate_adoption(
        resolved / "run.json",
        candidate_ref=candidate_ref,
        accepted_ref=accepted_ref,
        write=True,
    )
    return result["adoption"]


def print_report(root: Path, runs: Path) -> None:
    run_root = resolve_repo_path(root, runs)
    collected = report_module.collect_runs(run_root)
    if not collected:
        print("No run facts found.")
        return
    report_module.print_runs(collected)
    report_module.print_summary(collected)


def write_dashboard(root: Path, runs: Path, tasks: Path, output: Path, zh_output: Path | None = None) -> list[Path]:
    runs_root = resolve_repo_path(root, runs)
    tasks_root = resolve_repo_path(root, tasks)
    output_path = resolve_repo_path(root, output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    zh_path = resolve_repo_path(root, zh_output) if zh_output else dashboard_module.zh_output_path(output_path)
    zh_path.parent.mkdir(parents=True, exist_ok=True)

    collected = dashboard_module.collect_runs(runs_root, tasks_root)
    output_path.write_text(dashboard_module.dashboard_html(collected, "en"), encoding="utf-8")
    zh_path.write_text(dashboard_module.dashboard_html(collected, "zh-CN"), encoding="utf-8")
    return [output_path, zh_path]


def add_run_dir_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-dir", type=Path, default=None, help="Run directory. Defaults to runs/.current.json pointer.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shortcut CLI for the AI coding evaluation workflow.")
    parser.add_argument("--repo", type=Path, default=None, help="Evaluation repo root. Defaults to AI_EVAL_REPO or this script's repo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Prepare a run and set runs/.current.json")
    start.add_argument("--workflow", required=True, help="Workflow group id, such as baseline, plan-first, or tdd")
    start.add_argument("--task", required=True, help="Task id, matching benchmarks/tasks/{id}")
    start.add_argument("--run-id", default=None, help="Run id. Defaults to UTC timestamp.")
    start.add_argument("--model", default=None, help="Optional model label for run.json")

    current = subparsers.add_parser("current", help="Print current run metadata")
    add_run_dir_arg(current)

    target = subparsers.add_parser("target", help="Print target worktree path")
    add_run_dir_arg(target)

    env = subparsers.add_parser("env", help="Print hook environment exports")
    add_run_dir_arg(env)

    collect = subparsers.add_parser("collect", help="Collect tests, diff, and run evidence")
    add_run_dir_arg(collect)
    collect.add_argument("--reset-to-base", action="store_true", help="Checkout target.base_ref before running commands")
    collect.add_argument("--expect-fail", action="store_true", help="Treat failing required tests as expected")

    score = subparsers.add_parser("score", help="Write manual review scores and calculate score.json")
    add_run_dir_arg(score)
    score.add_argument("--init", action="store_true", help="Create a manual scoring draft score.json")
    score.add_argument("--set-review", nargs="+", metavar="DIMENSION=VALUE", help="Set manual review scores")
    score.add_argument("--manual-hard-gate", action="append", dest="manual_hard_gates", help="Add a manual hard gate")

    llm_review = subparsers.add_parser("llm-review", help="Use an OpenAI-compatible LLM reviewer")
    add_run_dir_arg(llm_review)
    llm_review.add_argument("--score-file", type=Path, default=None, help="Path to score.json")
    llm_review.add_argument("--base-url", default=llm_review_module.env_or_default("AI_EVAL_REVIEW_BASE_URL", llm_review_module.DEFAULT_BASE_URL))
    llm_review.add_argument("--model", default=llm_review_module.env_or_default("AI_EVAL_REVIEW_MODEL"))
    llm_review.add_argument("--api-key-env", default=llm_review_module.env_or_default("AI_EVAL_REVIEW_API_KEY_ENV", llm_review_module.DEFAULT_API_KEY_ENV))
    llm_review.add_argument("--response-mode", choices=["json_object", "json_schema"], default="json_object")
    llm_review.add_argument("--max-input-chars", type=int, default=int(llm_review_module.env_or_default("AI_EVAL_REVIEW_MAX_INPUT_CHARS", str(llm_review_module.DEFAULT_MAX_INPUT_CHARS))))
    llm_review.add_argument("--max-tokens", type=int, default=int(llm_review_module.env_or_default("AI_EVAL_REVIEW_MAX_TOKENS", str(llm_review_module.DEFAULT_MAX_TOKENS))))

    solution = subparsers.add_parser("solution-diff", help="Print candidate-vs-reference solution diff")
    add_run_dir_arg(solution)
    solution.add_argument("--color", choices=["auto", "always", "never"], default="auto")

    adoption = subparsers.add_parser("adoption", help="Calculate line-level adoption and update run.json")
    add_run_dir_arg(adoption)
    adoption.add_argument("--candidate-ref", default=None)
    adoption.add_argument("--accepted-ref", default=None)

    report = subparsers.add_parser("report", help="Print terminal report")
    report.add_argument("--runs", type=Path, default=Path("runs"))

    dashboard = subparsers.add_parser("dashboard", help="Generate static HTML dashboards")
    dashboard.add_argument("--runs", type=Path, default=Path("runs"))
    dashboard.add_argument("--tasks", type=Path, default=Path("benchmarks/tasks"))
    dashboard.add_argument("--output", type=Path, default=Path("reports/dashboard.html"))
    dashboard.add_argument("--zh-output", type=Path, default=None)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    root = resolve_root(args.repo)
    try:
        if args.command == "start":
            result = start_run(root, args.workflow, args.task, run_id=args.run_id, model=args.model)
            print(json.dumps(result, indent=2, sort_keys=True))
            print()
            print("Next:")
            eval_script = root / "scripts" / "eval.py"
            print(f'eval "$({shlex.quote(sys.executable)} {shlex.quote(str(eval_script))} env)"')
            print('cd "$AI_EVAL_TARGET_WORKTREE"')
            print("Use task.md in the run directory as the coding prompt. Do not read acceptance.md during coding.")
            return
        if args.command == "current":
            run_dir = resolve_run_dir(root, args.run_dir)
            print(json.dumps(current_metadata(root, run_dir), indent=2, sort_keys=True))
            return
        if args.command == "target":
            print(target_path(root, args.run_dir))
            return
        if args.command == "env":
            print(shell_env(root, args.run_dir), end="")
            return
        if args.command == "collect":
            result = collect_run(root, args.run_dir, reset_to_base=args.reset_to_base, expect_fail=args.expect_fail)
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        if args.command == "score":
            result = score_manual_run(
                root,
                args.run_dir,
                assignments=args.set_review,
                manual_hard_gates=args.manual_hard_gates,
                init=args.init,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        if args.command == "llm-review":
            result = llm_review_shortcut(
                root,
                args.run_dir,
                score_file=args.score_file,
                base_url=args.base_url,
                model=args.model,
                api_key_env=args.api_key_env,
                response_mode=args.response_mode,
                max_input_chars=args.max_input_chars,
                max_tokens=args.max_tokens,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        if args.command == "solution-diff":
            print(solution_diff(root, args.run_dir, color=args.color), end="")
            return
        if args.command == "adoption":
            result = adoption_run(root, args.run_dir, candidate_ref=args.candidate_ref, accepted_ref=args.accepted_ref)
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        if args.command == "report":
            print_report(root, args.runs)
            return
        if args.command == "dashboard":
            for path in write_dashboard(root, args.runs, args.tasks, args.output, args.zh_output):
                print(path)
            return
        raise ValueError(f"unsupported command: {args.command}")
    except (FileNotFoundError, FileExistsError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
