from pathlib import Path

DEFAULT_DB_PATH = "results/eval_results.db"
DEFAULT_WORKDIR = "workdir"
EVAL_ENTRY_CONFIG = "eval.yaml"
RESULT_JSON_SCHEMA_KEYS = ["tests"]
PREP_STATE_FILE = ".prep_state.json"

TASK_REPOS_SUBDIR = "task_repos"
TEST_REPOS_SUBDIR = "test_repos"


def get_project_root() -> Path:
    """Return the project root (directory containing pyproject.toml)."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()
