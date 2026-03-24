from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from task_eval.db.store import EvalStore


def generate_report(db_path: str | Path) -> dict:
    """Aggregate raw metrics from the database and return a structured report."""
    with EvalStore(db_path) as store:
        group_stats = store.query_group_stats()
        all_results = store.query_results()

    total_runs = len(all_results)
    unique_tasks = len({r["task_id"] for r in all_results})
    unique_tools = len({r["tool"] for r in all_results})
    unique_models = len({r["model"] for r in all_results})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_runs": total_runs,
            "total_groups": len(group_stats),
            "unique_tasks": unique_tasks,
            "unique_tools": unique_tools,
            "unique_models": unique_models,
        },
        "group_stats": group_stats,
    }


def render_markdown_report(report: dict, output_path: str | Path) -> None:
    """Render a structured report dict into a Markdown file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# AI 辅助编程工具评估报告")
    lines.append("")

    summary = report["summary"]
    lines.append("## 执行摘要")
    lines.append("")
    lines.append(f"- 生成时间：{report['generated_at']}")
    lines.append(f"- 总运行次数：{summary['total_runs']}")
    lines.append(f"- 分组数量：{summary['total_groups']}")
    lines.append(f"- 任务数量：{summary['unique_tasks']}")
    lines.append(f"- 工具数量：{summary['unique_tools']}")
    lines.append(f"- 模型数量：{summary['unique_models']}")
    lines.append("")

    groups = report["group_stats"]
    if groups:
        lines.append("## 组合对比")
        lines.append("")
        lines.append(
            "| task_id | tool | model | runs | avg_passed | avg_total "
            "| pass_rate | avg_time(s) | completion_rate |"
        )
        lines.append(
            "|---------|------|-------|------|------------|----------"
            "|-----------|-------------|-----------------|"
        )
        for g in groups:
            lines.append(
                f"| {g['task_id']} "
                f"| {g['tool']} "
                f"| {g['model']} "
                f"| {g['run_count']} "
                f"| {g['avg_tests_passed']:.1f} "
                f"| {g['avg_tests_total']:.1f} "
                f"| {g['pass_rate']:.2%} "
                f"| {g['avg_time_spent']:.1f} "
                f"| {g['completion_rate']:.2%} |"
            )
        lines.append("")
    else:
        lines.append("## 组合对比")
        lines.append("")
        lines.append("暂无评估数据。")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
