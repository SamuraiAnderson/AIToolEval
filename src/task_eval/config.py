from pathlib import Path

DEFAULT_DB_PATH = "results/eval_results.db"
DEFAULT_WORKDIR = "workdir"
EVAL_ENTRY_CONFIG = "eval.yaml"
GENERATE_ENTRY_CONFIG = "generate.yaml"
RESULT_JSON_SCHEMA_KEYS = ["tests"]
PREP_STATE_FILE = ".prep_state.json"

TASK_REPOS_SUBDIR = "task_repos"
TEST_REPOS_SUBDIR = "test_repos"


def task_repo_path(workdir: Path, task_id: str) -> Path:
    """Deterministic path for generated task repo, keyed by task_id."""
    return workdir / TASK_REPOS_SUBDIR / task_id


def get_project_root() -> Path:
    """Return the project root (directory containing pyproject.toml)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()
