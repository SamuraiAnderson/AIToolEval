import json

from task_eval.models import EvalResult, Task, TestCaseResult


class TestTask:
    def test_from_dict_roundtrip(self):
        data = {
            "id": "zstd-630",
            "task_repo": "https://github.com/facebook/zstd.git",
            "task_repo_ref": "dev",
            "test_repo": "https://github.com/eval-tests/zstd-630-tests.git",
            "test_repo_ref": "main",
            "metadata": {"difficulty": "medium"},
            "prompts_dir": "prompts",
        }
        task = Task.from_dict(data)
        assert task.id == "zstd-630"
        assert task.metadata["difficulty"] == "medium"
        assert task.to_dict() == data

    def test_defaults(self):
        task = Task(
            id="t1",
            task_repo="url",
            task_repo_ref="main",
            test_repo="url2",
            test_repo_ref="main",
        )
        assert task.metadata == {}
        assert task.prompts_dir == "prompts"


class TestTestCaseResult:
    def test_from_dict(self):
        data = {"name": "test_foo", "passed": True, "duration": 0.5, "error": None}
        tc = TestCaseResult.from_dict(data)
        assert tc.passed is True
        assert tc.duration == 0.5
        assert tc.to_dict() == data

    def test_with_error(self):
        tc = TestCaseResult(name="test_bar", passed=False, duration=1.2, error="fail")
        assert tc.error == "fail"


class TestEvalResult:
    def _make_result(self, **overrides) -> EvalResult:
        defaults = {
            "run_id": "abc-123",
            "task_id": "zstd-630",
            "tool": "claude-code",
            "model": "claude-3.5-sonnet",
            "run_index": 1,
            "timestamp": "2026-03-24T00:00:00",
            "tags": '{"format":"M1"}',
            "prompt_file": "standard.md",
            "prompt": "Fix the bug",
            "base_commit_sha": "aaa",
            "eval_commit_sha": "bbb",
            "tests_passed": 3,
            "tests_total": 4,
            "test_details": json.dumps([
                {"name": "t1", "passed": True, "duration": 0.1, "error": None},
                {"name": "t2", "passed": True, "duration": 0.2, "error": None},
                {"name": "t3", "passed": True, "duration": 0.3, "error": None},
                {"name": "t4", "passed": False, "duration": 0.4, "error": "AssertionError"},
            ]),
            "time_spent": 5.0,
            "success": False,
            "lines_added": 10,
            "lines_deleted": 2,
            "files_modified": 1,
            "patch": "+some code",
        }
        defaults.update(overrides)
        return EvalResult(**defaults)

    def test_roundtrip(self):
        r = self._make_result()
        d = r.to_dict()
        r2 = EvalResult.from_dict(d)
        assert r2.run_id == r.run_id
        assert r2.success == r.success

    def test_get_test_case_results(self):
        r = self._make_result()
        cases = r.get_test_case_results()
        assert len(cases) == 4
        assert cases[0].name == "t1"
        assert cases[3].passed is False

    def test_get_tags(self):
        r = self._make_result()
        assert r.get_tags() == {"format": "M1"}

    def test_get_tags_empty(self):
        r = self._make_result(tags="{}")
        assert r.get_tags() == {}
