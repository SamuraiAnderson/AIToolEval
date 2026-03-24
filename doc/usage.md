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
| `--workdir` | 否 | `workdir` | 工作目录 |

执行内容：

1. 克隆/拉取 task-test repo
2. 运行 `generate.sh` 生成被测代码库到 `workdir/task_repos/{task_id}/`
3. 记录 `base_commit_sha`（generate.sh 产生的初始 commit）
4. 将 prompt 完整打印到终端（用分隔线包围）
5. 将状态写入 `workdir/.prep_state.json`

如果省略 `--prompt`：
- 只有一个 prompt 文件时自动选择
- 多个时交互列出供选择

每次 `prep` 都会删除旧的生成目录并重新生成，确保干净的初始状态。

终端输出示例：

```
[prep] Ensuring test repo: workdir/local_ini_test_repo @ main
[prep] Generating task repo: workdir/task_repos/ini-parser-simple
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
[prep] Task repo ready: workdir/task_repos/ini-parser-simple
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
| `id` | 是 | 唯一任务 ID，同时决定被测代码库路径 `workdir/task_repos/{id}/` |
| `test_repo` | 是 | task-test repo 的 git URL（含生成器和验证测试） |
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

每个 task-test repo 是任务的**单一事实源**，同时负责生成被测代码库和验证 AI 产出。

### 5.1 目录结构

```
task-test-repo/
├── generate.yaml      # 生成器声明
├── generate.sh        # 生成被测代码库
├── skeleton/          # 代码模板
├── eval.yaml          # 验证入口声明
├── eval.sh            # 验证脚本
├── meta.md            # 问题权威描述
└── tests/             # 测试用例
```

### 5.2 generate.yaml

```yaml
entry: ./generate.sh
```

### 5.3 generate.sh

生成被测代码库的脚本。**必须**产出一个包含至少一次 commit 的 git 仓库。

```bash
#!/bin/bash
set -euo pipefail
OUTPUT_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cp -r "$SCRIPT_DIR/skeleton/." "$OUTPUT_DIR/"

cd "$OUTPUT_DIR"
git init
git config user.email "task-eval@local"
git config user.name "task-eval"
git add -A
git commit -m "initial task state"
```

合约要求：
- 接收 `$1` 为输出目录路径（由框架提供的空目录）
- 在 test repo 目录下执行
- 必须在输出目录中创建有效的 git 仓库并包含至少一次 commit
- 必须设置 `git config user.email` / `user.name`（确保在无全局配置的环境中正常工作）
- 退出码 0 表示成功

### 5.4 eval.yaml

```yaml
entry: ./eval.sh
result_file: results.json
```

### 5.5 eval.sh

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

### 5.6 results.json 格式

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

### 5.7 meta.md

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

每次 `prep` 都会删除旧的生成目录并重新生成，确保各轮之间互不干扰。

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
