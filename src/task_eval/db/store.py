from __future__ import annotations

import sqlite3
from pathlib import Path

from task_eval.models import EvalResult

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS eval_runs (
    run_id              TEXT PRIMARY KEY,
    task_id             TEXT NOT NULL,
    tool                TEXT NOT NULL,
    model               TEXT NOT NULL,
    run_index           INTEGER NOT NULL,
    timestamp           TEXT NOT NULL,
    tags                TEXT NOT NULL DEFAULT '{}',
    prompt_file         TEXT NOT NULL,
    prompt              TEXT NOT NULL,
    base_commit_sha     TEXT NOT NULL,
    eval_commit_sha     TEXT,
    tests_passed        INTEGER NOT NULL,
    tests_total         INTEGER NOT NULL,
    test_details        TEXT NOT NULL DEFAULT '[]',
    time_spent          REAL NOT NULL,
    success             INTEGER NOT NULL,
    lines_added         INTEGER NOT NULL DEFAULT 0,
    lines_deleted       INTEGER NOT NULL DEFAULT 0,
    files_modified      INTEGER NOT NULL DEFAULT 0,
    patch               TEXT
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_eval_group
ON eval_runs(task_id, tool, model);
"""

_INSERT_SQL = """
INSERT INTO eval_runs (
    run_id, task_id, tool, model, run_index, timestamp, tags,
    prompt_file, prompt, base_commit_sha, eval_commit_sha,
    tests_passed, tests_total, test_details, time_spent, success,
    lines_added, lines_deleted, files_modified, patch
) VALUES (
    :run_id, :task_id, :tool, :model, :run_index, :timestamp, :tags,
    :prompt_file, :prompt, :base_commit_sha, :eval_commit_sha,
    :tests_passed, :tests_total, :test_details, :time_spent, :success,
    :lines_added, :lines_deleted, :files_modified, :patch
);
"""

_GROUP_STATS_SQL = """
SELECT
    task_id,
    tool,
    model,
    COUNT(*)                                            AS run_count,
    AVG(tests_passed)                                   AS avg_tests_passed,
    AVG(tests_total)                                    AS avg_tests_total,
    SUM(tests_passed) * 1.0 / MAX(SUM(tests_total), 1) AS pass_rate,
    AVG(time_spent)                                     AS avg_time_spent,
    AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END)   AS completion_rate
FROM eval_runs
GROUP BY task_id, tool, model
ORDER BY task_id, tool, model;
"""


class EvalStore:
    def __init__(self, db_path: str | Path = "results/eval_results.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self._conn.execute(_CREATE_TABLE_SQL)
        self._conn.execute(_CREATE_INDEX_SQL)
        self._conn.commit()

    def save_result(self, result: EvalResult) -> None:
        params = result.to_dict()
        params["success"] = int(params["success"])
        self._conn.execute(_INSERT_SQL, params)
        self._conn.commit()

    def query_results(
        self,
        task_id: str | None = None,
        tool: str | None = None,
        model: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[str] = []
        if task_id is not None:
            clauses.append("task_id = ?")
            params.append(task_id)
        if tool is not None:
            clauses.append("tool = ?")
            params.append(tool)
        if model is not None:
            clauses.append("model = ?")
            params.append(model)

        sql = "SELECT * FROM eval_runs"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY timestamp"

        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def query_group_stats(self) -> list[dict]:
        rows = self._conn.execute(_GROUP_STATS_SQL).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> EvalStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
