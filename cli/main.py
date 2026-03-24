#!/usr/bin/env python3
"""Unified CLI entry point for task_eval: prep / run / report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure src/ is importable when running as `python cli/main.py`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from task_eval.config import (
    DEFAULT_DB_PATH,
    DEFAULT_WORKDIR,
    PREP_STATE_FILE,
    TASK_REPOS_SUBDIR,
    TEST_REPOS_SUBDIR,
)
from task_eval.runner import task_loader


# ---------------------------------------------------------------------------
# prep
# ---------------------------------------------------------------------------
def cmd_prep(args: argparse.Namespace) -> None:
    task = task_loader.load_task(args.task)
    workdir = Path(args.workdir)

    # clone / fetch repos
    print(f"[prep] Ensuring task repo: {task.task_repo} @ {task.task_repo_ref}")
    task_repo_path = task_loader.ensure_repo(
        task.task_repo, task.task_repo_ref, workdir, TASK_REPOS_SUBDIR,
    )

    print(f"[prep] Ensuring test repo: {task.test_repo} @ {task.test_repo_ref}")
    test_repo_path = task_loader.ensure_repo(
        task.test_repo, task.test_repo_ref, workdir, TEST_REPOS_SUBDIR,
    )

    # hard reset task repo
    print("[prep] Resetting task repo to clean state ...")
    task_loader.reset_repo(task_repo_path)
    base_sha = task_loader.get_head_sha(task_repo_path)
    print(f"[prep] base commit: {base_sha}")

    # load prompt
    if args.prompt:
        prompt_name = args.prompt
    else:
        available = task_loader.list_prompts(task)
        if not available:
            print("[prep] WARNING: no prompt files found in", task.prompts_dir)
            prompt_name = ""
        elif len(available) == 1:
            prompt_name = available[0]
        else:
            print("[prep] Available prompts:")
            for i, name in enumerate(available, 1):
                print(f"  {i}. {name}")
            choice = input("Select prompt number: ").strip()
            prompt_name = available[int(choice) - 1]

    prompt_content = ""
    if prompt_name:
        prompt_name, prompt_content = task_loader.load_prompt(task, prompt_name)
        print(f"[prep] prompt file: {prompt_name}")
        print()
        print("=" * 72)
        print(" PROMPT (copy below to your AI tool)")
        print("=" * 72)
        print()
        print(prompt_content)
        print()
        print("=" * 72)
    print()

    # write prep state
    state = {
        "task_id": task.id,
        "task_yaml": str(Path(args.task).resolve()),
        "task_repo_path": str(task_repo_path.resolve()),
        "test_repo_path": str(test_repo_path.resolve()),
        "base_commit_sha": base_sha,
        "prompt_file": prompt_name,
        "prompt": prompt_content,
    }
    state_path = workdir / PREP_STATE_FILE
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print(f"[prep] State saved to {state_path}")
    print(f"[prep] Task repo ready: {task_repo_path}")
    print("[prep] You may now use your AI tool to modify the code.")


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
def cmd_run(args: argparse.Namespace) -> None:
    workdir = Path(args.workdir)
    state_path = workdir / PREP_STATE_FILE

    if not state_path.exists():
        print(f"ERROR: prep state not found at {state_path}", file=sys.stderr)
        print("Run `task_eval prep` first.", file=sys.stderr)
        sys.exit(1)

    prep_state = json.loads(state_path.read_text())

    # load eval.yaml from test repo
    test_repo_path = Path(prep_state["test_repo_path"])
    eval_config = task_loader.load_eval_config(test_repo_path)

    # parse --tag key=value pairs
    tags: dict[str, str] = {}
    for tag_str in (args.tag or []):
        if "=" not in tag_str:
            print(f"WARNING: ignoring malformed tag: {tag_str}", file=sys.stderr)
            continue
        k, v = tag_str.split("=", 1)
        tags[k] = v

    from task_eval.runner.evaluator import record_run

    print(f"[run] task: {prep_state['task_id']}")
    print(f"[run] tool: {args.tool}, model: {args.model}, run_index: {args.run_index}")
    print(f"[run] Collecting diff ...")

    result = record_run(
        prep_state=prep_state,
        tool=args.tool,
        model=args.model,
        run_index=args.run_index,
        eval_config=eval_config,
        db_path=args.db,
        tags=tags,
    )

    print(f"[run] Tests: {result.tests_passed}/{result.tests_total} passed")
    print(f"[run] Success: {result.success}")
    print(f"[run] Time: {result.time_spent:.1f}s")
    print(f"[run] Diff: +{result.lines_added} -{result.lines_deleted} "
          f"({result.files_modified} files)")
    print(f"[run] Result saved: {result.run_id}")


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
def cmd_report(args: argparse.Namespace) -> None:
    from task_eval.report.generator import generate_report, render_markdown_report

    print(f"[report] Reading database: {args.db}")
    report = generate_report(args.db)
    print(f"[report] {report['summary']['total_runs']} runs, "
          f"{report['summary']['total_groups']} groups")

    render_markdown_report(report, args.output)
    print(f"[report] Report written to {args.output}")


# ---------------------------------------------------------------------------
# arg parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task_eval",
        description="AI-assisted programming tool evaluation framework",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # prep
    p_prep = sub.add_parser("prep", help="Prepare workspace and show prompt")
    p_prep.add_argument("--task", required=True, help="Path to task.yaml")
    p_prep.add_argument("--prompt", default=None, help="Prompt filename in prompts/")
    p_prep.add_argument("--workdir", default=DEFAULT_WORKDIR, help="Working directory")
    p_prep.set_defaults(func=cmd_prep)

    # run
    p_run = sub.add_parser("run", help="Collect diff, run tests, store results")
    p_run.add_argument("--tool", required=True, help="AI tool name")
    p_run.add_argument("--model", required=True, help="Model name")
    p_run.add_argument("--run-index", type=int, required=True, help="Run index")
    p_run.add_argument("--workdir", default=DEFAULT_WORKDIR, help="Working directory")
    p_run.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite database path")
    p_run.add_argument("--tag", action="append", help="Tag as key=value (repeatable)")
    p_run.set_defaults(func=cmd_run)

    # report
    p_report = sub.add_parser("report", help="Generate evaluation report")
    p_report.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite database path")
    p_report.add_argument("--output", default="results/report.md", help="Output path")
    p_report.set_defaults(func=cmd_report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
