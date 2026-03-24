from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse

import yaml

from task_eval.config import EVAL_ENTRY_CONFIG
from task_eval.models import Task


def load_task(yaml_path: str | Path) -> Task:
    """Parse a task.yaml file and return a Task dataclass."""
    yaml_path = Path(yaml_path)
    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    task_data = raw["task"]
    prompts_dir = str(yaml_path.parent / task_data.get("prompts_dir", "prompts"))

    return Task(
        id=task_data["id"],
        task_repo=task_data["task_repo"],
        task_repo_ref=task_data["task_repo_ref"],
        test_repo=task_data["test_repo"],
        test_repo_ref=task_data["test_repo_ref"],
        metadata=task_data.get("metadata", {}),
        prompts_dir=prompts_dir,
    )


def list_prompts(task: Task) -> list[str]:
    """List all available prompt markdown files for a task."""
    prompts_path = Path(task.prompts_dir)
    if not prompts_path.is_dir():
        return []
    return sorted(p.name for p in prompts_path.glob("*.md"))


def load_prompt(task: Task, prompt_name: str) -> tuple[str, str]:
    """Read a specific prompt file. Returns (filename, full content)."""
    prompt_path = Path(task.prompts_dir) / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}\n"
            f"Available: {list_prompts(task)}"
        )
    content = prompt_path.read_text(encoding="utf-8")
    return prompt_name, content


def _repo_dir_name(git_url: str, ref: str) -> str:
    """Derive a directory name from a git URL and ref.

    e.g. https://github.com/facebook/zstd.git + abc123
         -> facebook__zstd__abc123
    """
    parsed = urlparse(git_url)
    path = parsed.path.rstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = [p for p in path.split("/") if p]
    slug = "__".join(parts[-2:]) if len(parts) >= 2 else "__".join(parts)
    safe_ref = ref.replace("/", "_")
    return f"{slug}__{safe_ref}"


def ensure_repo(git_url: str, ref: str, workdir: Path, subdir: str) -> Path:
    """Clone (if needed) or fetch a git repo, then checkout the given ref."""
    target = workdir / subdir / _repo_dir_name(git_url, ref)
    target.parent.mkdir(parents=True, exist_ok=True)

    if (target / ".git").is_dir():
        subprocess.run(
            ["git", "fetch", "--all"],
            cwd=target,
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "clone", git_url, str(target)],
            check=True,
            capture_output=True,
        )

    subprocess.run(
        ["git", "checkout", ref],
        cwd=target,
        check=True,
        capture_output=True,
    )
    return target


def reset_repo(repo_path: Path) -> None:
    """Hard-reset and clean a repo to ensure a pristine working tree."""
    subprocess.run(
        ["git", "reset", "--hard"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )


def get_head_sha(repo_path: Path) -> str:
    """Return the current HEAD commit SHA."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_eval_config(test_repo_path: Path) -> dict:
    """Read eval.yaml from a task-test repo."""
    config_path = test_repo_path / EVAL_ENTRY_CONFIG
    if not config_path.exists():
        raise FileNotFoundError(
            f"task-test repo missing {EVAL_ENTRY_CONFIG}: {config_path}"
        )
    with open(config_path) as f:
        return yaml.safe_load(f)
