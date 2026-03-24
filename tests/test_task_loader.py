import os
import subprocess
from pathlib import Path

import pytest
import yaml

from task_eval.runner.task_loader import (
    _repo_dir_name,
    generate_task_repo,
    list_prompts,
    load_generate_config,
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


@pytest.fixture
def test_repo_with_generator(tmp_path: Path) -> Path:
    """Create a minimal task-test repo with generate.yaml, generate.sh, and skeleton."""
    repo = tmp_path / "test_repo"
    repo.mkdir()

    (repo / "generate.yaml").write_text("entry: ./generate.sh\n")

    skeleton = repo / "skeleton"
    skeleton.mkdir()
    (skeleton / "hello.txt").write_text("hello from skeleton\n")

    script = repo / "generate.sh"
    script.write_text(
        '#!/bin/bash\n'
        'set -euo pipefail\n'
        'OUTPUT_DIR="$1"\n'
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"\n'
        'cp -r "$SCRIPT_DIR/skeleton/." "$OUTPUT_DIR/"\n'
        'cd "$OUTPUT_DIR"\n'
        'git init\n'
        'git config user.email "test@test.com"\n'
        'git config user.name "Test"\n'
        'git add -A\n'
        'git commit -m "initial"\n'
    )
    os.chmod(str(script), 0o755)

    return repo


class TestLoadTask:
    def test_basic_load(self, task_dir: Path):
        task = load_task(task_dir / "task.yaml")
        assert task.id == "test-001"
        assert task.test_repo_ref == "v1"
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


class TestLoadGenerateConfig:
    def test_load(self, tmp_path: Path):
        config = {"entry": "./generate.sh"}
        (tmp_path / "generate.yaml").write_text(yaml.dump(config))
        loaded = load_generate_config(tmp_path)
        assert loaded["entry"] == "./generate.sh"

    def test_missing_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_generate_config(tmp_path)


class TestGenerateTaskRepo:
    def test_generates_git_repo(self, test_repo_with_generator: Path, tmp_path: Path):
        output = tmp_path / "generated"
        generate_task_repo(test_repo_with_generator, output)

        assert output.is_dir()
        assert (output / ".git").is_dir()
        assert (output / "hello.txt").exists()
        assert (output / "hello.txt").read_text() == "hello from skeleton\n"

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=output, capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert len(result.stdout.strip()) == 40

    def test_idempotent_regeneration(self, test_repo_with_generator: Path, tmp_path: Path):
        output = tmp_path / "generated"
        generate_task_repo(test_repo_with_generator, output)
        (output / "extra.txt").write_text("should be removed")

        generate_task_repo(test_repo_with_generator, output)
        assert not (output / "extra.txt").exists()
        assert (output / "hello.txt").exists()

    def test_missing_entry_script_raises(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "generate.yaml").write_text("entry: ./nonexistent.sh\n")

        output = tmp_path / "out"
        with pytest.raises(FileNotFoundError):
            generate_task_repo(repo, output)
