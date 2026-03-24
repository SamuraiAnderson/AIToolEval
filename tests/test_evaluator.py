import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from task_eval.models import TestCaseResult
from task_eval.runner.evaluator import collect_diff, run_eval, validate_result, record_run
from task_eval.models import EvalResult


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with an initial commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo, capture_output=True,
    )
    (repo / "main.c").write_text("int main() { return 0; }\n")
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo, capture_output=True,
    )
    return repo


class TestCollectDiff:
    def test_no_changes(self, git_repo: Path):
        added, deleted, files, patch = collect_diff(git_repo)
        assert added == 0
        assert deleted == 0
        assert files == 0
        assert patch is None

    def test_with_changes(self, git_repo: Path):
        (git_repo / "main.c").write_text("int main() { return 42; }\n")
        added, deleted, files, patch = collect_diff(git_repo)
        assert added >= 1
        assert deleted >= 1
        assert files == 1
        assert patch is not None
        assert "42" in patch

    def test_new_file(self, git_repo: Path):
        (git_repo / "new.c").write_text("void foo() {}\n")
        added, deleted, files, patch = collect_diff(git_repo)
        assert added == 0
        assert files == 0


class TestRunEval:
    def test_successful_eval(self, tmp_path: Path):
        test_repo = tmp_path / "test_repo"
        test_repo.mkdir()
        task_repo = tmp_path / "task_repo"
        task_repo.mkdir()

        results_data = {
            "tests": [
                {"name": "test_a", "passed": True, "duration": 0.1, "error": None},
                {"name": "test_b", "passed": False, "duration": 0.5, "error": "fail"},
            ]
        }

        eval_script = test_repo / "eval.sh"
        eval_script.write_text(
            f'#!/bin/bash\n'
            f'echo \'{json.dumps(results_data)}\' > "{test_repo}/results.json"\n'
        )
        os.chmod(str(eval_script), 0o755)

        config = {"entry": "./eval.sh", "result_file": "results.json"}
        cases, elapsed = run_eval(task_repo, test_repo, config)

        assert len(cases) == 2
        assert cases[0].name == "test_a"
        assert cases[0].passed is True
        assert cases[1].passed is False
        assert cases[1].error == "fail"
        assert elapsed > 0

    def test_missing_entry_script(self, tmp_path: Path):
        config = {"entry": "./nonexistent.sh", "result_file": "results.json"}
        with pytest.raises(FileNotFoundError):
            run_eval(tmp_path, tmp_path, config)

    def test_missing_result_file(self, tmp_path: Path):
        test_repo = tmp_path / "test_repo"
        test_repo.mkdir()

        eval_script = test_repo / "eval.sh"
        eval_script.write_text("#!/bin/bash\necho 'no output'\n")
        os.chmod(str(eval_script), 0o755)

        config = {"entry": "./eval.sh", "result_file": "results.json"}
        with pytest.raises(FileNotFoundError, match="result file"):
            run_eval(tmp_path, test_repo, config)


class TestValidateResult:
    def _make_result(self, **kw) -> EvalResult:
        defaults = dict(
            run_id="r1", task_id="t1", tool="t", model="m",
            run_index=1, timestamp="now", tags="{}", prompt_file="p.md",
            prompt="p", base_commit_sha="a", eval_commit_sha=None,
            tests_passed=2, tests_total=3, test_details="[]",
            time_spent=1.0, success=False, lines_added=0,
            lines_deleted=0, files_modified=0, patch=None,
        )
        defaults.update(kw)
        return EvalResult(**defaults)

    def test_valid(self):
        assert validate_result(self._make_result()) is True

    def test_passed_exceeds_total(self):
        assert validate_result(self._make_result(tests_passed=5, tests_total=3)) is False

    def test_negative_time(self):
        assert validate_result(self._make_result(time_spent=-1)) is False
