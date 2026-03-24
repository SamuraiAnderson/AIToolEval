# AI 辅助编程工具评估方案

## 1. 概述

本方案设计一个**多维度的 AI 辅助编程工具评估框架**，用于量化评估不同工具组合在实际开发任务中的表现。
### 1.1 评估公式

```
得分 = f(task, task-unit-test, task description markdown M, AI 辅助编程工具 A, 模型 L)
```

**变量说明：**
- `task`: 具体开发任务（如修复某个 Issue）
- `task-unit-test`: 任务对应的单元测试套件
- `task description markdown M`: 任务描述的 Markdown 格式（多种变体）
- `AI 辅助编程工具 A`: 被评估的 AI 工具（如 Claude Code、Cursor）
- `模型 L`: 工具使用的底层 AI 模型（如 Claude-3.5-Sonnet、GPT-4）

---

## 2. 评估架构

### 2.1 整体流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        评估流程                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ 1. 任务准备  │                                               │
│  │ - task       │                                               │
│  │ - unit-test  │                                               │
│  │ - markdown M │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ 2. 工具执行  │                                               │
│  │ - 工具 A     │                                               │
│  │ - 模型 L     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ 3. 结果验证  │                                               │
│  │ - 运行测试   │                                               │
│  │ - 计算得分   │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ 4. 数据分析  │                                               │
│  │ - 对比分析   │                                               │
│  │ - 报告生成   │                                               │
│  └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 评估矩阵

| 维度 | 变量 | 示例值 |
|------|------|--------|
| **任务描述格式 (M)** | M1, M2, M3... | 标准 Issue 格式、结构化 Prompt、示例驱动格式 |
| **AI 工具 (A)** | A1, A2, A3... | Claude Code、Cursor、OpenHands |
| **底层模型 (L)** | L1, L2, L3... | Claude-3.5-Sonnet、GPT-4o、Gemini-2.0 |
| **任务类型 (T)** | T1, T2, T3... | Bug 修复、功能开发、代码重构 |

---

## 3. 任务描述 Markdown 格式设计

### 3.1 格式 M1：标准 Issue 格式

```markdown
---
task_id: {repo}_{issue_number}
repo: {owner}/{repo_name}
type: bug_fix | feature | refactor
difficulty: easy | medium | hard
---

# 任务描述

## 问题说明
{Issue 原始描述}

## 预期行为
{修复后应有的行为}

## 复现步骤
1. {步骤 1}
2. {步骤 2}
3. {步骤 3}

## 测试要求
- [ ] 通过现有测试
- [ ] 添加新测试用例（如需要）

## 验收标准
- [ ] 代码编译通过
- [ ] 所有单元测试通过
- [ ] 无新增警告
```

### 3.2 格式 M2：结构化 Prompt 格式

```markdown
---
task_id: {task_id}
context:
  repo: {repo_name}
  language: {language}
  framework: {framework}
constraints:
  time_limit: {minutes}
  file_limit: {max_files}
---

# 角色定义
你是一位 {语言} 专家，负责修复代码问题。

# 任务目标
{明确的任务目标}

# 可用资源
- 源代码目录：{src_dir}
- 测试目录：{test_dir}
- 文档目录：{doc_dir}

# 输出要求
1. 修改的文件列表
2. 每个文件的修改内容（diff 格式）
3. 修改说明

# 执行步骤
1. 分析问题
2. 定位相关代码
3. 生成修复方案
4. 实现修复
5. 验证修复
```

### 3.3 格式 M3：示例驱动格式

````markdown
---
task_id: {task_id}
---

# 任务：{任务名称}

## 输入示例
```{language}
// 问题代码示例
{problematic_code}
```

## 期望输出
```{language}
// 修复后的代码
{expected_code}
```

## 任务说明
{详细说明}

## 测试用例
```{language}
// 测试代码
{test_code}
```
````

---

## 4. AI 辅助编程工具适配

### 4.1 工具列表

| 工具 ID | 工具名称 | 类型 | 适配方式 |
|--------|----------|------|----------|
| A1 | Claude Code | CLI | 直接调用 |
| A2 | Cursor | IDE | 插件调用 |
| A3 | OpenHands | Agent 框架 | API 调用 |
| A4 | GitHub Copilot | 补全工具 | IDE 插件 |
| A5 | Codeium | 补全工具 | IDE 插件 |

### 4.2 工具调用接口

#### Claude Code
```bash
claude "根据以下任务描述完成修复：$(cat task_description.md)"
```

#### Cursor
```python
# 通过 Cursor API 或 IDE 插件
cursor.chat(prompt=task_description,
context=codebase)
```

#### OpenHands
```python
from openhands
import Agent

agent = Agent(model="claude-3.5-sonnet")
result = agent.run(task_description)
```

---

## 5. 评估指标

### 5.1 核心指标

| 指标 | 符号 | 计算方式 | 说明 |
|------|------|----------|------|
| **测试通过率** | `PASS` | `passed_tests / total_tests` | 代码正确性 |
| **任务完成率** | `CPL` | `completed_tasks / total_tasks` | 任务完成度 |
| **代码接受率** | `ACC` | `accepted_lines / total_lines` | 代码质量 |
| **时间效率** | `TIME` | `completion_time` | 完成耗时 |
| **交互轮数** | `TURN` | `conversation_turns` | 交互复杂度 |
| **Token 消耗** | `TOKEN` | `prompt_tokens + completion_tokens` | 模型资源消耗 |
| **费用成本** | `COST` | `token_cost_usd + tool_cost_usd` | 经济成本（美元） |

### 5.2 综合得分计算

```
单次得分 s_i(M, A, L) = w1 * PASS_i + w2 * CPL_i + w3 * ACC_i + w4 * (1/TIME_norm_i) + w5 * (1/TURN_norm_i) + w6 * (1/COST_norm_i)

其中:
- w1, w2, w3, w4, w5, w6 为权重系数
- TIME_norm, TURN_norm, COST_norm 为归一化后的值
```

### 5.3 权重建议

| 场景 | w1(PASS) | w2(CPL) | w3(ACC) | w4(TIME) | w5(TURN) | w6(COST) |
|------|----------|---------|---------|----------|----------|----------|
| **生产环境** | 0.4 | 0.3 | 0.2 | 0.03 | 0.02 | 0.05 |
| **快速原型** | 0.2 | 0.3 | 0.2 | 0.15 | 0.05 | 0.1 |
| **学习辅助** | 0.2 | 0.2 | 0.2 | 0.15 | 0.15 | 0.1 |

### 5.4 成本计算规则（P0）

```
TOKEN_i = prompt_tokens_i + completion_tokens_i
COST_i  = TOKEN_i / 1_000_000 * model_price_per_1m_tokens + tool_fixed_cost
```

说明：
- `model_price_per_1m_tokens` 建议按模型官方单价配置（可区分输入/输出）
- `tool_fixed_cost` 用于计入工具侧固定费用（如 API 网关费，默认可为 0）
- 报告需同时输出 `avg_total_tokens` 与 `avg_cost_usd`

### 5.5 重复实验统计（P0）

对每个组合 `(M, A, L)`，至少重复执行 `N=3~5` 次，推荐默认 `N=5`。

```
均值:      mean_score(M, A, L) = (1/N) * Σ s_i
方差:      var_score(M, A, L)  = (1/N) * Σ (s_i - mean_score)^2
标准差:    std_score(M, A, L)  = sqrt(var_score)
```

报告输出必须包含：
- `run_count`（该组合实际运行次数）
- `mean_score`（均值）
- `var_score`（方差）
- `std_score`（标准差，可选但建议）

---

## 6. 实施步骤

### 6.1 步骤 1：任务准备

```python
# 任务数据结构
task = {
    "id": "zstd-630",
    "repo": "facebook/zstd",
    "issue": "Issue 描述文本",
    "issue_markdown_format": "M1",  # M1, M2, M3
    "test_suite": {
        "path": "tests/test_zstd.py",
        "cases": ["test_compress", "test_decompress"]
    },
    "expected_patch": "可选的参考补丁",
    "difficulty": "medium"
}
```

### 6.2 步骤 2：环境配置

```bash
# 1. 克隆代码库
git clone https://github.com/facebook/zstd.git
cd zstd

# 2. 创建测试环境
docker run -v $(pwd):/workspace -it eval_env

# 3. 安装依赖
make install

# 4. 验证测试套件
make test
```

### 6.3 步骤 3：执行评估

```python
import sqlite3
import uuid
from datetime import datetime

def init_db(db_path="results/eval_results.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS eval_runs (
        run_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        tool TEXT NOT NULL,
        model TEXT NOT NULL,
        markdown_format TEXT NOT NULL,
        run_index INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        success INTEGER NOT NULL,
        time_spent REAL NOT NULL,
        interaction_turns INTEGER NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        cost_usd REAL NOT NULL,
        tests_passed INTEGER NOT NULL,
        tests_total INTEGER NOT NULL,
        lines_added INTEGER NOT NULL,
        lines_deleted INTEGER NOT NULL,
        files_modified INTEGER NOT NULL,
        score REAL NOT NULL,
        patch TEXT
    );
    """)
    conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_eval_group
    ON eval_runs(task_id, tool, model, markdown_format);
    """)
    conn.commit()
    return conn

def evaluate_once(task, tool, model, markdown_format, run_index):
    """执行单次评估（一次 run）"""
    result = {
        "run_id": str(uuid.uuid4()),
        "run_index": run_index,
        "task_id": task["id"],
        "tool": tool,
        "model": model,
        "markdown_format": markdown_format,
        "timestamp": datetime.now().isoformat(),
        
        # 执行结果
        "success": False,
        "time_spent": 0,  # 秒
        "interaction_turns": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "tests_passed": 0,
        "tests_total": len(task["test_suite"]["cases"]),
        "patch": None,
        
        # 代码质量指标
        "lines_added": 0,
        "lines_deleted": 0,
        "files_modified": 0,
    }
    
    # 执行任务
    start_time = datetime.now()
    
    # 1. 准备任务描述
    task_description = format_task_description(
        task,
        markdown_format
    )
    
    # 2. 调用工具
    response = tool.execute(task_description)
    
    # 3. 获取结果
    result["patch"] = response.patch
    result["interaction_turns"] = response.turns
    result["prompt_tokens"] = response.usage.prompt_tokens
    result["completion_tokens"] = response.usage.completion_tokens
    result["total_tokens"] = result["prompt_tokens"] + result["completion_tokens"]
    
    # 4. 应用补丁并运行测试
    apply_patch(response.patch)
    test_result = run_tests(task["test_suite"])
    
    result["tests_passed"] = test_result.passed
    result["success"] = test_result.all_passed
    result["time_spent"] = (datetime.now() - start_time).total_seconds()
    
    # 5. 分析代码变更
    result["lines_added"], result["lines_deleted"] = analyze_diff(response.patch)
    result["files_modified"] = len(response.patch.files)

    # 5.1 成本计算
    result["cost_usd"] = calc_cost_usd(
        model=model,
        prompt_tokens=result["prompt_tokens"],
        completion_tokens=result["completion_tokens"],
    )
    
    # 6. 计算单次分数（示例，按你的权重配置替换）
    result["score"] = calc_score(result)

    return result

def save_result(conn, result):
    conn.execute("""
    INSERT INTO eval_runs (
        run_id, task_id, tool, model, markdown_format, run_index, timestamp,
        success, time_spent, interaction_turns, prompt_tokens, completion_tokens,
        total_tokens, cost_usd, tests_passed, tests_total,
        lines_added, lines_deleted, files_modified, score, patch
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result["run_id"], result["task_id"], result["tool"], result["model"],
        result["markdown_format"], result["run_index"], result["timestamp"],
        int(result["success"]), result["time_spent"], result["interaction_turns"],
        result["prompt_tokens"], result["completion_tokens"], result["total_tokens"],
        result["cost_usd"], result["tests_passed"], result["tests_total"],
        result["lines_added"], result["lines_deleted"], result["files_modified"],
        result["score"], result["patch"]
    ))
    conn.commit()

def evaluate_group(task, tool, model, markdown_format, repeats=5):
    """对同一组 (M, A, L) 重复执行 3~5 次并写入数据库"""
    if repeats < 3 or repeats > 5:
        raise ValueError("repeats 必须在 [3, 5] 之间")

    conn = init_db()
    for run_index in range(1, repeats + 1):
        result = evaluate_once(task, tool, model, markdown_format, run_index)
        save_result(conn, result)
    conn.close()
```

### 6.4 步骤 4：结果汇总

```python
def generate_report(db_path="results/eval_results.db"):
    """从数据库聚合，输出每组 (M, A, L) 的均值与方差"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
    SELECT
        task_id,
        tool,
        model,
        markdown_format,
        COUNT(*) AS run_count,
        AVG(score) AS mean_score,
        AVG(score * score) - AVG(score) * AVG(score) AS var_score,
        AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) AS completion_rate,
        AVG(time_spent) AS avg_time,
        AVG(interaction_turns) AS avg_turns,
        AVG(total_tokens) AS avg_total_tokens,
        AVG(cost_usd) AS avg_cost_usd,
        SUM(tests_passed) * 1.0 / SUM(tests_total) AS pass_rate
    FROM eval_runs
    GROUP BY task_id, tool, model, markdown_format
    ORDER BY task_id, tool, model, markdown_format
    """).fetchall()

    detailed_groups = [dict(r) for r in rows]
    report = {
        "summary": {
            "total_groups": len(detailed_groups),
            "min_repeats_required": 3,
            "recommended_repeats": 5,
            "db_path": db_path,
        },
        "group_stats": detailed_groups,
    }
    conn.close()
    return report
```

---

## 7. 输出格式

### 7.1 单次评估结果

```json
{
  "run_id": "37f6f1a7-11cb-4fd2-a77a-96e1a88a2f5d",
  "run_index": 1,
  "task_id": "zstd-630",
  "tool": "Claude Code",
  "model": "Claude-3.5-Sonnet",
  "markdown_format": "M1",
  "timestamp": "2026-03-24T11:00:00",
  "success": true,
  "time_spent": 185.5,
  "interaction_turns": 8,
  "prompt_tokens": 12450,
  "completion_tokens": 2680,
  "total_tokens": 15130,
  "cost_usd": 0.48,
  "tests_passed": 12,
  "tests_total": 12,
  "patch": {
    "files_modified": 2,
    "lines_added": 45,
    "lines_deleted": 12
  },
  "score": 0.92
}
```

### 7.2 汇总报告

```markdown
# AI 辅助编程工具评估报告

## 执行摘要
- 评估时间：2026-03-24
- 分组总数：30（按 task_id + M + A + L）
- 每组重复次数：5（最小要求 3）
- 工具数量：3
- 模型数量：3
- Markdown 格式：3

## 组合对比（含均值与方差）

| task_id | 格式(M) | 工具(A) | 模型(L) | run_count | mean_score | var_score | avg_total_tokens | avg_cost_usd | pass_rate | completion_rate |
|---------|---------|---------|---------|-----------|------------|-----------|------------------|--------------|-----------|-----------------|
| zstd-630 | M1 | Claude Code | Claude-3.5-Sonnet | 5 | 0.91 | 0.0008 | 15800 | 0.52 | 0.92 | 1.00 |
| zstd-630 | M2 | Cursor | GPT-4o | 5 | 0.84 | 0.0031 | 13150 | 0.41 | 0.83 | 0.80 |
| zstd-630 | M3 | OpenHands | Gemini-2.0 | 5 | 0.79 | 0.0052 | 11920 | 0.29 | 0.77 | 0.60 |

## 结论与建议
{分析结论}
```

---

## 8. 示例：完整评估流程

### 8.1 任务定义

```yaml
# tasks/zstd-630.yaml
task:
  id: zstd-630
  repo: facebook/zstd
  issue: |
    Compression fails when input size exceeds 4GB
  description_markdown_format: M1
  test_suite:
    path: tests/test_compression.py
    cases:
      - test_compress_small
      - test_compress_large
      - test_decompress_small
      - test_decompress_large
  difficulty: medium
  expected_time:
    30  # minutes
```

### 8.2 执行评估

```bash
# 运行评估
python evaluate.py \
  --task tasks/zstd-630.yaml \
  --tool claude-code \
  --model claude-3.5-sonnet \
  --format M1 \
  --repeats 5 \
  --db results/eval_results.db \
  --output results/zstd-630.json
```

### 8.3 生成报告

```bash
# 汇总所有结果
python generate_report.py \
  --db results/eval_results.db \
  --output report.md
```

---

## 9. 质量保证

### 9.1 控制变量

| 变量 | 控制方法 |
|------|----------|
| 开发者水平 | 同一开发者完成所有工具测试，或随机分配 |
| 环境一致性 | 使用相同 Docker 镜像 |
| 任务难度 | 预先评估任务难度，均衡分配 |
| 时间限制 | 统一时间限制 |

### 9.2 数据验证

```python
def validate_result(result):
    """验证评估结果的有效性"""
    checks = [
        result["tests_passed"] <= result["tests_total"],
        result["time_spent"] > 0,
        result["interaction_turns"] >= 0,
        result["prompt_tokens"] >= 0,
        result["completion_tokens"] >= 0,
        result["total_tokens"] == result["prompt_tokens"] + result["completion_tokens"],
        result["cost_usd"] >= 0,
        result["patch"] is not None if result["success"] else True,
    ]
    return all(checks)
```

### 9.3 重复实验一致性校验（P0）

```python
def validate_group_repeats(group_rows, min_repeats=3):
    """校验每组 (task_id, M, A, L) 至少运行 min_repeats 次"""
    return len(group_rows) >= min_repeats

def validate_report_group_stats(group_stat):
    """校验聚合结果包含均值与方差字段"""
    required_fields = [
        "task_id", "tool", "model", "markdown_format",
        "run_count", "mean_score", "var_score", "avg_total_tokens", "avg_cost_usd"
    ]
    return all(field in group_stat for field in required_fields) and \
           group_stat["run_count"] >= 3
```

---

## 10. 附录

### 10.1 术语表

| 术语 | 说明 |
|------|------|
| task | 具体的开发任务，如修复 Issue |
| task-unit-test | 用于验证任务完成的单元测试 |
| task description markdown | 任务描述的 Markdown 格式 |
| AI 辅助编程工具 | Claude Code、Cursor 等工具 |
| 模型 | 工具使用的底层 AI 模型 |

### 10.2 参考资源

- [SWE-bench](https://www.swebench.com/)
- [Multi-SWE-bench](https://github.com/multi-swe-bench/multi-swe-bench)


