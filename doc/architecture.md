# 框架设计文档

## 1. 设计目标

task_eval 是一个 AI 辅助编程工具的评估框架。核心问题：给定一个开发任务，不同的 AI 工具 + 模型 + prompt 组合，产出的代码质量如何？

框架本身不调用任何 AI 工具，而是提供一套标准化的流程：准备环境 → 人工/AI 完成任务 → 自动运行测试 → 记录原始结果。

## 2. 三层分离架构

```
本项目 (task_eval)                外部 git 仓库
┌─────────────────────┐       ┌──────────────────┐
│ tasks/zstd-630/     │──────>│ task repo        │  AI 工具在此工作
│ ├── task.yaml       │       │ (被测代码库)      │
│ └── prompts/        │       └──────────────────┘
│     ├── standard.md │
│     └── structured.md│      ┌──────────────────┐
│  (怎么问 AI 工具)    │──────>│ task-test repo   │  验证集（黑箱）
└─────────────────────┘       │ ├── meta.md      │  问题权威描述
                              │ ├── eval.yaml    │  声明入口
                              │ ├── eval.sh      │  自带加载器
                              │ └── tests/       │  测试用例
                              └──────────────────┘
```

| 层级 | 位置 | 内容 | 性质 |
|------|------|------|------|
| 任务元数据 | 本项目 `tasks/*/task.yaml` | git URL、ref、metadata | 配置 |
| Prompt 变体 | 本项目 `tasks/*/prompts/*.md` | 给 AI 工具的实际 prompt | 可实验变量 |
| Ground Truth | task-test repo `meta.md` | 问题权威定义、Root Cause | 客观事实（不给 AI 看） |
| 验证测试 | task-test repo `eval.sh` + `tests/` | 黑箱测试，判断修改是否正确 | 对 AI 不可见 |
| 被测代码 | task repo | AI 工具在上面工作的真实代码库 | 外部仓库 |

## 3. 项目结构

```
task_eval/
├── src/task_eval/
│   ├── config.py              # 配置常量
│   ├── models.py              # 数据模型：Task, TestCaseResult, EvalResult
│   ├── db/
│   │   └── store.py           # SQLite 存储：EvalStore
│   ├── runner/
│   │   ├── task_loader.py     # YAML 加载 + git 仓库管理 + prompt 加载
│   │   └── evaluator.py       # diff 采集 + 执行 eval.sh + 结果解析 + 存库
│   └── report/
│       └── generator.py       # SQL 聚合 + Markdown 报告
├── cli/
│   └── main.py                # 统一 CLI 入口：prep / run / report
├── tasks/                     # 任务定义目录
├── workdir/                   # 运行时 git clone 目标
├── results/                   # 数据库 + 报告输出
└── tests/                     # 框架自身的单元测试
```

## 4. 数据模型

### 4.1 Task

```python
@dataclass
class Task:
    id: str                  # 任务 ID，如 "zstd-630"
    task_repo: str           # 被测代码库 git URL
    task_repo_ref: str       # 分支/tag/commit
    test_repo: str           # task-test 验证集 git URL
    test_repo_ref: str       # 分支/tag/commit
    metadata: dict           # 可选：difficulty, language, expected_time
    prompts_dir: str         # prompts 目录路径
```

### 4.2 EvalResult

每次评估运行的完整记录，也是数据库 `eval_runs` 表的行模型。

| 字段 | 类型 | 说明 |
|------|------|------|
| `run_id` | TEXT PK | UUID，每次运行唯一 |
| `task_id` | TEXT | 关联的任务 ID |
| `tool` | TEXT | 所用 AI 工具名称 |
| `model` | TEXT | 所用模型名称 |
| `run_index` | INTEGER | 同一组合的第几次运行 |
| `timestamp` | TEXT | ISO 8601 时间戳 |
| `tags` | TEXT | 自由标签 JSON 字典 |
| `prompt_file` | TEXT | 使用的 prompt 文件名 |
| `prompt` | TEXT | prompt 完整原文 |
| `base_commit_sha` | TEXT | prep 时的原始 commit |
| `eval_commit_sha` | TEXT | AI 修改后的 commit（无新提交时为 NULL） |
| `tests_passed` | INTEGER | 通过的测试数 |
| `tests_total` | INTEGER | 总测试数 |
| `test_details` | TEXT | JSON 序列化的每个用例结果 |
| `time_spent` | REAL | eval.sh 执行耗时（秒） |
| `success` | INTEGER | 是否全部通过（0/1） |
| `lines_added` | INTEGER | 新增行数 |
| `lines_deleted` | INTEGER | 删除行数 |
| `files_modified` | INTEGER | 修改文件数 |
| `patch` | TEXT | git diff 原文 |

### 4.3 TestCaseResult

单个测试用例的结果，序列化后存入 `test_details` 字段。

```python
@dataclass
class TestCaseResult:
    name: str               # 用例名
    passed: bool            # 是否通过
    duration: float         # 耗时（秒）
    error: str | None       # 失败时的错误信息
```

## 5. task-test repo 合约

框架与 task-test repo 之间通过标准化接口通信，框架不关心测试的语言、框架或编译方式。

### 5.1 必需文件

```
task-test-repo/
├── eval.yaml          # 声明入口脚本和结果文件路径
├── eval.sh            # 执行入口，接收 task repo 路径作为 $1
├── meta.md            # 问题权威描述（供 prompt 作者参考）
└── tests/             # 测试用例（结构由 eval.sh 决定）
```

### 5.2 eval.yaml

```yaml
entry: ./eval.sh
result_file: results.json
```

### 5.3 eval.sh 合约

- 接收一个参数：task repo 的绝对路径
- 在 test repo 目录下执行
- 自行处理：测试注入/关联、依赖安装、编译、执行
- 将结果写入 `result_file` 指定的 JSON 文件

### 5.4 results.json 格式

```json
{
  "tests": [
    {"name": "test_compress_small", "passed": true,  "duration": 0.12, "error": null},
    {"name": "test_compress_large", "passed": false, "duration": 2.34, "error": "AssertionError: ..."}
  ]
}
```

每个测试条目必须包含 `name` 和 `passed` 字段，`duration` 和 `error` 可选。

### 5.5 信息流：meta.md → prompts

```
task-test repo                    本项目 tasks/*/prompts/
┌────────────┐                    ┌──────────────────────┐
│ meta.md    │ ──(人工参考)──>    │ standard.md          │  直白转述
│ (客观事实)  │                    │ structured.md        │  角色 + 步骤引导
│            │                    │ minimal.md           │  只给关键信息
└────────────┘                    └──────────────────────┘
```

`meta.md` 包含问题的 Root Cause、受影响文件等答案级信息，不直接给 AI 看。prompt 作者阅读 `meta.md` 后，用不同风格手工撰写 prompt 文件。

## 6. 模块设计

### 6.1 task_loader.py — 任务加载与仓库管理

| 函数 | 职责 |
|------|------|
| `load_task(yaml_path)` | 解析 task.yaml → `Task` |
| `list_prompts(task)` | 列出可用 prompt 文件 |
| `load_prompt(task, name)` | 读取 prompt 内容 |
| `ensure_repo(url, ref, workdir, subdir)` | clone/fetch + checkout |
| `reset_repo(path)` | `git reset --hard && git clean -fd` |
| `get_head_sha(path)` | 获取当前 HEAD SHA |
| `load_eval_config(test_repo_path)` | 读取 eval.yaml |

工作目录布局：

```
workdir/
├── task_repos/
│   └── facebook__zstd__dev/          # {owner}__{repo}__{ref}
└── test_repos/
    └── eval-tests__zstd-630__main/
```

### 6.2 evaluator.py — 评估执行

关键顺序：**diff 前置 → 测试后置**，避免 eval.sh 的编译产物污染 diff。

| 函数 | 职责 |
|------|------|
| `collect_diff(repo_path)` | `git diff HEAD` + `git diff --numstat`，返回 patch 和统计 |
| `run_eval(task_path, test_path, config)` | 执行 eval.sh、解析 results.json |
| `validate_result(result)` | `tests_passed <= tests_total` 等基本校验 |
| `record_run(prep_state, ...)` | 完整流水线：diff → test → 组装 → 校验 → 存库 |

### 6.3 store.py — SQLite 存储

`EvalStore` 类，支持上下文管理器：

| 方法 | 职责 |
|------|------|
| `save_result(result)` | 插入一条 `eval_runs` 记录 |
| `query_results(task_id, tool, model)` | 按条件过滤查询 |
| `query_group_stats()` | 按 `(task_id, tool, model)` 分组聚合 |

聚合指标：`run_count`, `avg_tests_passed`, `avg_tests_total`, `pass_rate`, `avg_time_spent`, `completion_rate`。

### 6.4 generator.py — 报告生成

- `generate_report(db_path)` → 结构化字典（summary + group_stats）
- `render_markdown_report(report, output_path)` → Markdown 文件

## 7. CLI 两阶段设计

因为评估流程中存在"AI 工具工作"这一人工介入阶段，CLI 拆分为 `prep` 和 `run` 两步，中间留出空间给 AI 工具修改代码。

```
prep ──→ [AI 工具工作] ──→ run ──→ report
```

### 7.1 prep 阶段

1. clone/fetch task repo 和 test repo
2. `git reset --hard && git clean -fd` 清理 task repo
3. 记录 `base_commit_sha`
4. 打印 prompt 到终端供用户复制
5. 写入 `.prep_state.json`

### 7.2 run 阶段

1. 读取 `.prep_state.json`
2. **先** `collect_diff()` 采集纯净 diff
3. **后** `run_eval()` 执行 eval.sh
4. 获取 `eval_commit_sha`
5. 组装 `EvalResult` 存入 SQLite

### 7.3 report 阶段

从 SQLite 聚合所有结果，输出 Markdown 报告。

## 8. 技术选型

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 主语言 |
| sqlite3 | 结果存储（标准库） |
| argparse | CLI 解析（标准库） |
| subprocess | 调用 git 和 eval.sh（标准库） |
| dataclasses | 数据模型（标准库） |
| PyYAML | YAML 解析 |
| pytest | 框架自身的单元测试 |
