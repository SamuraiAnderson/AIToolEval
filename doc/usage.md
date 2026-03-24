# 使用指南

## 1. 安装

```bash
# 克隆项目
git clone <repo_url>
cd task_eval

# 安装（开发模式）
pip install -e ".[dev]"
```

依赖：Python 3.11+、git。

## 2. 快速上手

完整的评估流程分为四步：定义任务 → 准备环境 → AI 工具工作 → 运行测试。

```bash
# 1. 准备环境，打印 prompt
python cli/main.py prep \
  --task tasks/ini-parser-simple/task.yaml \
  --prompt standard.md

# 2. 将终端输出的 prompt 复制到 AI 工具，AI 修改代码...

# 3. AI 工作完成后，运行测试并存储结果
python cli/main.py run \
  --tool claude-code \
  --model claude-3.5-sonnet \
  --run-index 1

# 4. 生成报告
python cli/main.py report --output results/report.md
```

## 3. CLI 参考

### 3.1 task_eval prep

准备工作环境，打印 prompt 供用户复制。

```bash
python cli/main.py prep --task <path> [--prompt <name>] [--workdir <dir>]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--task` | 是 | — | task.yaml 文件路径 |
| `--prompt` | 否 | 交互选择 | prompts/ 下的文件名 |
| `--workdir` | 否 | `workdir` | git clone 目标目录 |

执行内容：

1. 克隆/拉取 task repo 和 test repo
2. 强制清理 task repo（`git reset --hard && git clean -fd`）
3. 记录 `base_commit_sha`
4. 将 prompt 完整打印到终端（用分隔线包围）
5. 将状态写入 `workdir/.prep_state.json`

如果省略 `--prompt`：
- 只有一个 prompt 文件时自动选择
- 多个时交互列出供选择

终端输出示例：

```
[prep] task repo ready: workdir/task_repos/workdir__local_ini_task_repo__main
[prep] base commit: abc123def456
[prep] prompt file: standard.md

========================================================================
 PROMPT (copy below to your AI tool)
========================================================================

# Code Generation: C INI Parser

## Task
Implement a simple INI parser in C by completing `ini_get_value()`.
...

========================================================================

[prep] State saved to workdir/.prep_state.json
[prep] You may now use your AI tool to modify the code.
```

### 3.2 task_eval run

AI 工具完成工作后，采集 diff、运行测试、存储结果。

```bash
python cli/main.py run \
  --tool <name> --model <name> --run-index <int> \
  [--workdir <dir>] [--db <path>] [--tag key=value ...]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--tool` | 是 | — | AI 工具名（如 `claude-code`, `cursor`） |
| `--model` | 是 | — | 模型名（如 `claude-3.5-sonnet`） |
| `--run-index` | 是 | — | 本组合第几次运行 |
| `--workdir` | 否 | `workdir` | 对应 prep 的 workdir |
| `--db` | 否 | `results/eval_results.db` | SQLite 数据库路径 |
| `--tag` | 否 | — | 自由标签，可重复 |

`--tag` 示例：

```bash
--tag prompt_style=cot --tag temperature=0.7
```

执行内容：

1. 读取 `.prep_state.json`
2. `git diff` 采集代码变更（在测试之前，确保不受编译产物污染）
3. 调用 task-test repo 的 `eval.sh` 执行测试
4. 解析 `results.json`
5. 组装完整 `EvalResult` 存入 SQLite

终端输出示例：

```
[run] task: ini-parser-simple
[run] tool: claude-code, model: claude-3.5-sonnet, run_index: 1
[run] Collecting diff ...
[run] Tests: 4/4 passed
[run] Success: True
[run] Time: 3.2s
[run] Diff: +15 -3 (2 files)
[run] Result saved: a1b2c3d4-...
```

### 3.3 task_eval report

从数据库聚合所有评估结果，生成 Markdown 报告。

```bash
python cli/main.py report [--db <path>] [--output <path>]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--db` | 否 | `results/eval_results.db` | 数据库路径 |
| `--output` | 否 | `results/report.md` | 报告输出路径 |

报告按 `(task_id, tool, model)` 分组，包含：

- run_count — 运行次数
- avg_tests_passed / avg_tests_total — 平均通过数
- pass_rate — 测试通过率
- avg_time_spent — 平均耗时
- completion_rate — 全部通过的比例

## 4. 添加新任务

### 4.1 创建任务目录

```
tasks/my-task/
├── task.yaml
└── prompts/
    ├── standard.md
    └── structured.md
```

### 4.2 编写 task.yaml

```yaml
task:
  id: my-task
  task_repo: https://github.com/owner/repo.git
  task_repo_ref: main                # commit hash 或 branch/tag
  test_repo: https://github.com/owner/repo-tests.git
  test_repo_ref: main
  metadata:                          # 可选
    difficulty: medium
    language: python
    expected_time: 20
```

字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 唯一任务 ID |
| `task_repo` | 是 | 被测代码库 git URL |
| `task_repo_ref` | 是 | 具体 commit/branch/tag |
| `test_repo` | 是 | 验证测试集 git URL |
| `test_repo_ref` | 是 | 测试 repo 的 ref |
| `metadata` | 否 | 自由元数据字典 |

### 4.3 编写 prompt 文件

阅读 task-test repo 中的 `meta.md`（问题权威描述），然后用不同风格编写 prompt：

**standard.md** — 直白描述问题：

```markdown
# Bug Fix: Something is broken

## Problem
描述问题现象...

## Expected Behavior
期望的正确行为...

## Reproduction
1. 步骤一
2. 步骤二
```

**structured.md** — 角色扮演 + 步骤引导：

```markdown
# Role
You are a {language} expert.

# Task
Fix the bug in {repo} where ...

# Steps
1. Locate ...
2. Identify ...
3. Fix ...
```

## 5. 创建 task-test repo

每个 task-test repo 需要三个文件：

### 5.1 eval.yaml

```yaml
entry: ./eval.sh
result_file: results.json
```

### 5.2 eval.sh

```bash
#!/bin/bash
TASK_REPO_PATH="$1"

# 示例：Python 项目
export PYTHONPATH="$TASK_REPO_PATH/src:$PYTHONPATH"
cd "$(dirname "$0")"
python -m pytest tests/ --tb=short -q > /dev/null 2>&1

# 生成标准化结果
python generate_results.py
```

脚本必须：
- 接收 task repo 路径作为 `$1`
- 在 test repo 目录下执行
- 将测试结果写入 `result_file` 指定的 JSON 文件

### 5.3 results.json 格式

```json
{
  "tests": [
    {"name": "test_basic", "passed": true, "duration": 0.05, "error": null},
    {"name": "test_edge", "passed": false, "duration": 0.12, "error": "AssertionError: ..."}
  ]
}
```

每个条目：
- `name`（必填）：测试用例名
- `passed`（必填）：是否通过
- `duration`（可选）：耗时秒数
- `error`（可选）：失败时的错误信息

### 5.4 meta.md

供 prompt 作者参考的问题权威描述。应包含：

- 问题现象
- Root Cause（根本原因）
- 受影响的文件
- 复现步骤
- 验收标准

此文件不会被框架使用，也不应直接展示给 AI 工具。

## 6. 多轮评估工作流

对同一任务用不同 prompt 或不同工具重复评估：

```bash
# 第一轮：标准 prompt + Claude Code
python cli/main.py prep --task tasks/ini-parser-simple/task.yaml --prompt standard.md
# ... AI 工具工作 ...
python cli/main.py run --tool claude-code --model claude-3.5-sonnet --run-index 1

# 第二轮：结构化 prompt + Claude Code
python cli/main.py prep --task tasks/ini-parser-simple/task.yaml --prompt structured.md
# ... AI 工具工作 ...
python cli/main.py run --tool claude-code --model claude-3.5-sonnet --run-index 2

# 第三轮：标准 prompt + Cursor
python cli/main.py prep --task tasks/ini-parser-simple/task.yaml --prompt standard.md
# ... AI 工具工作 ...
python cli/main.py run --tool cursor --model gpt-4o --run-index 1 \
  --tag prompt_style=standard

# 生成汇总报告
python cli/main.py report
```

每次 `prep` 都会强制重置 task repo 到干净状态，确保各轮之间互不干扰。

## 7. 数据查询

### 7.1 直接查询 SQLite

```bash
sqlite3 results/eval_results.db
```

```sql
-- 查看所有运行
SELECT run_id, task_id, tool, model, tests_passed, tests_total, success
FROM eval_runs ORDER BY timestamp;

-- 按工具对比通过率
SELECT tool, model,
       COUNT(*) AS runs,
       AVG(tests_passed * 1.0 / tests_total) AS avg_pass_rate
FROM eval_runs
GROUP BY tool, model;

-- 查看某次运行的 prompt
SELECT prompt FROM eval_runs WHERE run_id = 'xxx';

-- 查看某次运行的 patch
SELECT patch FROM eval_runs WHERE run_id = 'xxx';
```

### 7.2 Python API

```python
from task_eval.db.store import EvalStore

with EvalStore("results/eval_results.db") as store:
    # 按条件查询
    results = store.query_results(task_id="ini-parser-simple", tool="claude-code")

    # 分组统计
    stats = store.query_group_stats()
    for g in stats:
        print(f"{g['tool']} / {g['model']}: "
              f"pass_rate={g['pass_rate']:.0%}, "
              f"runs={g['run_count']}")
```

## 8. 运行测试

```bash
# 运行框架自身的单元测试
python -m pytest tests/ -v
```
