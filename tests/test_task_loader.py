import tempfile
from pathlib import Path

import pytest
import yaml

from task_eval.runner.task_loader import (
    _repo_dir_name,
    list_prompts,
    load_prompt,
    load_task,
    load_eval_config,
)


@pytest.fixture
def task_dir(tmp_path: Path) -> Path:
    """Create a minimal task directory with task.yaml and prompts."""
    task_data = {
        "task": {
            "id": "test-001",
            "task_repo": "https://github.com/owner/repo.git",
            "task_repo_ref": "main",
            "test_repo": "https://github.com/owner/repo-tests.git",
            "test_repo_ref": "v1",
            "metadata": {"difficulty": "easy"},
        }
    }
    yaml_path = tmp_path / "task.yaml"
    yaml_path.write_text(yaml.dump(task_data))

    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "standard.md").write_text("# Standard\nFix the bug.")
    (prompts / "structured.md").write_text("# Role\nYou are an expert.")

    return tmp_path


class TestLoadTask:
    def test_basic_load(self, task_dir: Path):
        task = load_task(task_dir / "task.yaml")
        assert task.id == "test-001"
        assert task.task_repo_ref == "main"
        assert task.metadata["difficulty"] == "easy"
        assert "prompts" in task.prompts_dir

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_task(tmp_path / "nonexistent.yaml")


class TestPrompts:
    def test_list_prompts(self, task_dir: Path):
        task = load_task(task_dir / "task.yaml")
        names = list_prompts(task)
        assert names == ["standard.md", "structured.md"]

    def test_load_prompt(self, task_dir: Path):
        task = load_task(task_dir / "task.yaml")
        name, content = load_prompt(task, "standard.md")
        assert name == "standard.md"
        assert "Fix the bug" in content

    def test_load_missing_prompt(self, task_dir: Path):
        task = load_task(task_dir / "task.yaml")
        with pytest.raises(FileNotFoundError):
            load_prompt(task, "nonexistent.md")

    def test_list_prompts_no_dir(self, tmp_path: Path):
        task_data = {
            "task": {
                "id": "no-prompts",
                "task_repo": "url",
                "task_repo_ref": "main",
                "test_repo": "url2",
                "test_repo_ref": "main",
            }
        }
        yaml_path = tmp_path / "task.yaml"
        yaml_path.write_text(yaml.dump(task_data))
        task = load_task(yaml_path)
        assert list_prompts(task) == []


class TestRepoDirName:
    def test_github_url(self):
        name = _repo_dir_name("https://github.com/facebook/zstd.git", "abc123")
        assert name == "facebook__zstd__abc123"

    def test_branch_with_slash(self):
        name = _repo_dir_name("https://github.com/org/repo.git", "feature/foo")
        assert name == "org__repo__feature_foo"

    def test_no_git_suffix(self):
        name = _repo_dir_name("https://github.com/org/repo", "main")
        assert name == "org__repo__main"


class TestLoadEvalConfig:
    def test_load(self, tmp_path: Path):
        config = {"entry": "./eval.sh", "result_file": "results.json"}
        (tmp_path / "eval.yaml").write_text(yaml.dump(config))
        loaded = load_eval_config(tmp_path)
        assert loaded["entry"] == "./eval.sh"

    def test_missing_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_eval_config(tmp_path)
