import json
import tempfile
from pathlib import Path

import pytest

from task_eval.db.store import EvalStore
from task_eval.models import EvalResult


def _make_result(
    run_id: str = "r1",
    task_id: str = "zstd-630",
    tool: str = "claude-code",
    model: str = "claude-3.5-sonnet",
    run_index: int = 1,
    tests_passed: int = 3,
    tests_total: int = 4,
    success: bool = False,
) -> EvalResult:
    return EvalResult(
        run_id=run_id,
        task_id=task_id,
        tool=tool,
        model=model,
        run_index=run_index,
        timestamp="2026-03-24T00:00:00",
        tags="{}",
        prompt_file="standard.md",
        prompt="Fix the bug",
        base_commit_sha="aaa",
        eval_commit_sha=None,
        tests_passed=tests_passed,
        tests_total=tests_total,
        test_details="[]",
        time_spent=5.0,
        success=success,
        lines_added=10,
        lines_deleted=2,
        files_modified=1,
        patch=None,
    )


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


class TestEvalStore:
    def test_save_and_query(self, db_path: Path):
        with EvalStore(db_path) as store:
            store.save_result(_make_result(run_id="r1"))
            store.save_result(_make_result(run_id="r2", run_index=2))

            results = store.query_results(task_id="zstd-630")
            assert len(results) == 2

    def test_query_filters(self, db_path: Path):
        with EvalStore(db_path) as store:
            store.save_result(_make_result(run_id="r1", tool="cursor"))
            store.save_result(_make_result(run_id="r2", tool="claude-code"))

            results = store.query_results(tool="cursor")
            assert len(results) == 1
            assert results[0]["tool"] == "cursor"

    def test_query_no_results(self, db_path: Path):
        with EvalStore(db_path) as store:
            results = store.query_results(task_id="nonexistent")
            assert results == []

    def test_group_stats(self, db_path: Path):
        with EvalStore(db_path) as store:
            store.save_result(
                _make_result(run_id="r1", tests_passed=4, tests_total=4, success=True)
            )
            store.save_result(
                _make_result(run_id="r2", run_index=2, tests_passed=3, tests_total=4, success=False)
            )

            stats = store.query_group_stats()
            assert len(stats) == 1
            g = stats[0]
            assert g["task_id"] == "zstd-630"
            assert g["run_count"] == 2
            assert g["avg_tests_passed"] == 3.5
            assert g["completion_rate"] == 0.5

    def test_duplicate_run_id_raises(self, db_path: Path):
        with EvalStore(db_path) as store:
            store.save_result(_make_result(run_id="dup"))
            with pytest.raises(Exception):
                store.save_result(_make_result(run_id="dup"))

    def test_creates_parent_dirs(self, tmp_path: Path):
        deep_path = tmp_path / "a" / "b" / "c" / "test.db"
        with EvalStore(deep_path) as store:
            store.save_result(_make_result())
            assert deep_path.exists()
