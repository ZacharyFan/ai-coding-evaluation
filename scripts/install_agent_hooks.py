#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class HookFile:
    source: Path
    destination: Path


HOOK_FILES = {
    "codex": (
        HookFile(
            source=Path("integrations/codex/config.example.toml"),
            destination=Path(".codex/config.toml"),
        ),
        HookFile(
            source=Path("integrations/codex/hooks.example.json"),
            destination=Path(".codex/hooks.json"),
        ),
    ),
    "claude": (
        HookFile(
            source=Path("integrations/claude-code/settings.example.json"),
            destination=Path(".claude/settings.local.json"),
        ),
    ),
}


def resolve_repo(repo: Path | None) -> Path:
    env_repo = os.environ.get("AI_EVAL_REPO")
    candidate = repo or (Path(env_repo) if env_repo else REPO_ROOT)
    resolved = candidate.expanduser().resolve()
    if not (resolved / "integrations").exists():
        raise FileNotFoundError(
            f"evaluation repo not found: {resolved}. Pass --repo or run eval env first."
        )
    return resolved


def resolve_target(target: Path | None) -> Path:
    env_target = os.environ.get("AI_EVAL_TARGET_WORKTREE")
    candidate = target or (Path(env_target) if env_target else None)
    if candidate is None:
        raise FileNotFoundError(
            'target worktree not found. Run `eval "$(python -m scripts.eval env)"` first, '
            "or pass --target /path/to/target."
        )
    resolved = candidate.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"target worktree does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"target worktree is not a directory: {resolved}")
    return resolved


def run_git(target: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_worktree(target: Path) -> bool:
    result = run_git(target, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def is_tracked(target: Path, relative_path: Path) -> bool:
    if not is_git_worktree(target):
        return False
    result = run_git(target, "ls-files", "--error-unmatch", relative_path.as_posix())
    return result.returncode == 0


def local_exclude_path(target: Path) -> Path | None:
    if not is_git_worktree(target):
        return None
    result = run_git(target, "rev-parse", "--git-path", "info/exclude")
    if result.returncode != 0:
        return None
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = target / path
    return path


def ensure_local_exclude(target: Path, relative_paths: list[Path]) -> Path | None:
    exclude_path = local_exclude_path(target)
    if exclude_path is None:
        return None

    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    lines = existing.splitlines()
    additions = [path.as_posix() for path in relative_paths if path.as_posix() not in lines]
    if not additions:
        return exclude_path

    prefix = existing
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    exclude_path.write_text(prefix + "\n".join(additions) + "\n", encoding="utf-8")
    return exclude_path


def install_file(repo: Path, target: Path, hook_file: HookFile, *, force: bool) -> Path:
    source = repo / hook_file.source
    destination = target / hook_file.destination
    if not source.exists():
        raise FileNotFoundError(f"hook template not found: {source}")
    if is_tracked(target, hook_file.destination):
        raise RuntimeError(
            f"refusing to modify tracked target hook config: {hook_file.destination.as_posix()}"
        )

    content = source.read_text(encoding="utf-8")
    if destination.exists():
        existing = destination.read_text(encoding="utf-8")
        if existing == content:
            return destination
        if not force:
            raise FileExistsError(
                f"hook config already exists with different content: {destination}. "
                "Pass --force to overwrite untracked generated files."
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def selected_agents(agent: str) -> tuple[str, ...]:
    if agent == "all":
        return ("codex", "claude")
    return (agent,)


def install_agent_hooks(
    *,
    repo: Path,
    target: Path,
    agent: str = "all",
    force: bool = False,
) -> dict[str, list[str] | str | None]:
    installed: list[Path] = []
    for name in selected_agents(agent):
        for hook_file in HOOK_FILES[name]:
            installed.append(install_file(repo, target, hook_file, force=force))

    relative_paths = [path.relative_to(target) for path in installed]
    exclude_path = ensure_local_exclude(target, relative_paths)
    return {
        "target": str(target),
        "installed": [path.as_posix() for path in relative_paths],
        "local_exclude": str(exclude_path) if exclude_path else None,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install run-scoped Claude Code and Codex hook files into a target worktree."
    )
    parser.add_argument(
        "--agent",
        choices=["all", "codex", "claude"],
        default="all",
        help="Agent hook files to install. Defaults to both Codex and Claude Code.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Evaluation repo root. Defaults to AI_EVAL_REPO or this script's repo.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Target worktree. Defaults to AI_EVAL_TARGET_WORKTREE.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing untracked generated hook files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        result = install_agent_hooks(
            repo=resolve_repo(args.repo),
            target=resolve_target(args.target),
            agent=args.agent,
            force=args.force,
        )
    except (FileNotFoundError, FileExistsError, NotADirectoryError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None

    print(f"Installed hook files into {result['target']}:")
    for path in result["installed"]:
        print(f"- {path}")
    if result["local_exclude"]:
        print(f"Updated local git exclude: {result['local_exclude']}")


if __name__ == "__main__":
    main()
