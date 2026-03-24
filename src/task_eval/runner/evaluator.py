from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from task_eval.config import PREP_STATE_FILE, RESULT_JSON_SCHEMA_KEYS
from task_eval.db.store import EvalStore
from task_eval.models import EvalResult, TestCaseResult


def collect_diff(task_repo_path: Path) -> tuple[int, int, int, str | None]:
    """Collect git diff BEFORE running tests so build artifacts don't pollute it.

    Returns (lines_added, lines_deleted, files_modified, patch_text).
    """
    diff_result = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=task_repo_path,
        capture_output=True,
        text=True,
    )
    patch = diff_result.stdout.strip() or None

    numstat_result = subprocess.run(
        ["git", "diff", "--numstat", "HEAD"],
        cwd=task_repo_path,
        capture_output=True,
        text=True,
    )

    lines_added = 0
    lines_deleted = 0
    files_modified = 0
    for line in numstat_result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            added = parts[0]
            deleted = parts[1]
            if added != "-":
                lines_added += int(added)
            if deleted != "-":
                lines_deleted += int(deleted)
            files_modified += 1

    return lines_added, lines_deleted, files_modified, patch


def run_eval(
    task_repo_path: Path,
    test_repo_path: Path,
    eval_config: dict,
) -> tuple[list[TestCaseResult], float]:
    """Execute the task-test repo's entry script and parse results.

    Returns (test_case_results, elapsed_seconds).
    """
    entry = eval_config.get("entry", "./eval.sh")
    result_file = eval_config.get("result_file", "results.json")

    entry_path = test_repo_path / entry
    if not entry_path.exists():
        raise FileNotFoundError(f"eval entry script not found: {entry_path}")

    os.chmod(str(entry_path), 0o755)

    start = time.monotonic()
    proc = subprocess.run(
        [str(entry_path), str(task_repo_path)],
        cwd=test_repo_path,
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - start

    result_path = test_repo_path / result_file
    if not result_path.exists():
        raise FileNotFoundError(
            f"eval script did not produce result file: {result_path}\n"
            f"stdout: {proc.stdout[-500:] if proc.stdout else ''}\n"
            f"stderr: {proc.stderr[-500:] if proc.stderr else ''}"
        )

    with open(result_path) as f:
        raw = json.load(f)

    for key in RESULT_JSON_SCHEMA_KEYS:
        if key not in raw:
            raise ValueError(f"results.json missing required key: {key!r}")

    cases = [
        TestCaseResult(
            name=t["name"],
            passed=bool(t["passed"]),
            duration=float(t.get("duration", 0)),
            error=t.get("error"),
        )
        for t in raw["tests"]
    ]
    return cases, elapsed


def validate_result(result: EvalResult) -> bool:
    """Basic sanity checks on an EvalResult."""
    return all([
        result.tests_passed <= result.tests_total,
        result.time_spent >= 0,
    ])


def record_run(
    prep_state: dict,
    tool: str,
    model: str,
    run_index: int,
    eval_config: dict,
    db_path: str | Path,
    tags: dict | None = None,
) -> EvalResult:
    """Full evaluation pipeline: diff -> test -> assemble -> validate -> store.

    Args:
        prep_state: Loaded from .prep_state.json (has paths, base_sha, prompt).
        tool: AI tool name (e.g. "claude-code").
        model: Model name (e.g. "claude-3.5-sonnet").
        run_index: Run index for this (task, tool, model) combo.
        eval_config: Parsed eval.yaml from the test repo.
        db_path: Path to SQLite database.
        tags: Optional free-form tags dict.
    """
    task_repo_path = Path(prep_state["task_repo_path"])
    test_repo_path = Path(prep_state["test_repo_path"])

    # 1) eval_commit_sha (HEAD after AI tool modified code)
    from task_eval.runner.task_loader import get_head_sha
    eval_commit_sha = get_head_sha(task_repo_path)
    base_sha = prep_state["base_commit_sha"]
    if eval_commit_sha == base_sha:
        eval_commit_sha = None  # no new commits

    # 2) collect diff BEFORE running tests
    lines_added, lines_deleted, files_modified, patch = collect_diff(task_repo_path)

    # 3) run tests AFTER diff collection
    cases, elapsed = run_eval(task_repo_path, test_repo_path, eval_config)

    tests_passed = sum(1 for c in cases if c.passed)
    tests_total = len(cases)

    result = EvalResult(
        run_id=str(uuid.uuid4()),
        task_id=prep_state["task_id"],
        tool=tool,
        model=model,
        run_index=run_index,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=json.dumps(tags or {}, ensure_ascii=False),
        prompt_file=prep_state["prompt_file"],
        prompt=prep_state["prompt"],
        base_commit_sha=base_sha,
        eval_commit_sha=eval_commit_sha,
        tests_passed=tests_passed,
        tests_total=tests_total,
        test_details=json.dumps([c.to_dict() for c in cases], ensure_ascii=False),
        time_spent=round(elapsed, 3),
        success=(tests_passed == tests_total),
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        files_modified=files_modified,
        patch=patch,
    )

    if not validate_result(result):
        raise ValueError(f"EvalResult failed validation: {result.run_id}")

    with EvalStore(db_path) as store:
        store.save_result(result)

    return result
