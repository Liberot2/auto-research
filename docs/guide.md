# Auto Research 定时任务框架 - 开发指南

## 项目结构

```
auto-research/
├── .claude/skills/              # Claude Code Skills 定义目录
│   ├── arxiv-tracker/
│   │   ├── SKILL.md             # Skill 定义（必须）
│   │   └── assets/              # 可选的模板等资源文件
│   │       └── report-template.md
│   ├── web-monitor/
│   │   └── SKILL.md
│   └── daily-summary/
│       └── SKILL.md
├── config/
│   └── tasks.yaml               # 任务配置：关联 Skill + 定时参数
├── src/
│   ├── cli.py                   # CLI 入口
│   ├── core/
│   │   ├── agent.py             # Agent 封装（Claude Agent SDK query()）
│   │   └── runner.py            # 任务运行器（构建 slash command → 调用 Agent）
│   └── scheduler/
│       └── windows.py           # Windows 任务计划程序集成
├── logs/                        # 执行日志输出目录
└── .venv/                       # Python 虚拟环境
```

## 运作原理

### 整体流程

```
Windows 任务计划程序 (schtasks)
  │
  │  到达预定时间，触发执行
  ▼
CLI: python -m src.cli run <task_name>
  │
  ▼
TaskRunner.run_task(task_name)
  │
  │  1. 从 config/tasks.yaml 读取任务配置
  │     获取 skill 名称 + parameters
  │
  │  2. 构建 slash command prompt
  │     例: /arxiv-tracker keywords=[LLM,agent] max_papers=5
  │
  ▼
Agent.run(prompt)
  │
  │  ClaudeAgentOptions:
  │    setting_sources = ["project", "local"]   ← 自动加载 .claude/skills/
  │    permission_mode = "bypassPermissions"     ← 无需人工确认
  │    max_turns = 10
  │
  │  SDK 的 query() 接收到 slash command 后：
  │    → 匹配 .claude/skills/arxiv-tracker/SKILL.md
  │    → 按 SKILL.md 中定义的 Workflow 执行
  │    → 可调用 WebSearch、文件读写等内置工具
  │
  ▼
AgentResponse (text, cost, duration, ...)
  │
  │  保存执行日志到 logs/<task>_<timestamp>.txt
  ▼
TaskResult → CLI 输出 JSON 结果
```

### 关键组件说明

#### 1. Skill (.claude/skills/)

Skill 是 Claude Code 的原生能力扩展机制。每个 Skill 是 `.claude/skills/` 下的一个目录，包含一个 `SKILL.md` 文件。SDK 通过 `setting_sources=["project"]` 自动发现和加载这些 Skill。

当 Agent 接收到 slash command 形式的 prompt（如 `/arxiv-tracker keywords=[LLM]`）时，SDK 会自动匹配对应的 Skill 并按其定义的 Workflow 执行。

#### 2. 任务配置 (config/tasks.yaml)

将任务名称映射到 Skill + 参数 + 时间表：

```yaml
tasks:
  morning_papers:                    # 任务名称（自定义）
    skill: arxiv_tracker             # 对应 .claude/skills/arxiv-tracker/ 的 Skill
    description: "追踪 ArXiv 最新论文"
    schedule: "daily 08:00"          # Windows 计划表达式
    enabled: false                   # 是否启用
    parameters:                      # 传递给 slash command 的参数
      keywords: ["large language model", "agent"]
      max_papers: 5
```

- `skill` 字段：对应 `.claude/skills/` 下的目录名（下划线 `_` 会自动转为连字符 `-` 以匹配 slash command 格式）
- `parameters`：在执行时会被拼接到 slash command 中，如 `keywords=[LLM,agent] max_papers=5`

#### 3. Agent (src/core/agent.py)

对 `claude_agent_sdk` 的 `query()` API 的封装，核心配置：

| 参数 | 值 | 说明 |
|------|-----|------|
| `setting_sources` | `["project", "local"]` | 加载 `.claude/` 目录下的 Skills、Settings 等 |
| `permission_mode` | `"bypassPermissions"` | 无人值守模式，自动批准所有工具调用 |
| `max_turns` | `10` | 最大对话轮次 |

#### 4. TaskRunner (src/core/runner.py)

任务执行引擎，职责：

1. 读取 `config/tasks.yaml` 中的任务配置
2. 将 `skill` + `parameters` 拼接为 slash command prompt
3. 创建 Agent 并执行
4. 将结果日志写入 `logs/` 目录

#### 5. Windows 任务计划 (src/scheduler/windows.py)

通过 `schtasks` 命令将 Python CLI 注册为 Windows 系统定时任务。支持的计划格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| `daily HH:MM` | `daily 08:00` | 每天指定时间 |
| `interval MM` | `interval 60` | 每隔 N 分钟 |
| `onstartup` | `onstartup` | 系统启动时 |

## CLI 命令

```bash
# 列出所有已配置的任务
python -m src.cli list

# 列出所有可用的 Skills
python -m src.cli skills

# 手动运行单个任务
python -m src.cli run morning_papers

# 运行所有已启用的任务
python -m src.cli run

# 注册 Windows 定时任务
python -m src.cli schedule add morning_papers --at "daily 08:00"

# 列出已注册的 Windows 定时任务
python -m src.cli schedule list

# 删除 Windows 定时任务
python -m src.cli schedule remove morning_papers

# 详细日志模式
python -m src.cli -v run morning_papers
```

## 开发新任务：Step by Step

假设要创建一个「GitHub 仓库星标监控」任务，定期检查指定仓库的新 star 数并生成报告。

### Step 1: 创建 Skill

使用 Claude Code 的 `skill-creator` 工具创建，或手动创建。

目录结构：

```
.claude/skills/github-star-monitor/
└── SKILL.md
```

创建 SKILL.md 文件：

```markdown
---
name: github-star-monitor
description: |
  Monitor GitHub repository star counts and growth trends.
  Generate reports showing star history and growth rate analysis.
  Triggers: "github stars", "repo monitor", "仓库星标", "star monitor".
---

# GitHub Star Monitor

Monitor GitHub repository star growth and generate trend reports.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repos` | array | `["anthropics/claude-code"]` | GitHub repositories to monitor (owner/repo format) |
| `report_dir` | string | `reports` | Directory to save monitoring reports |

## Workflow

1. **Fetch**: For each repo in `repos`, use WebSearch to find current star count.
   Query: `github.com <owner>/<repo> stars`
2. **History**: Read previous monitoring data from `reports/star-history.json` if exists.
3. **Compare**: Calculate star growth since last check.
4. **Report**: Generate markdown report with growth summary, save to `report_dir`.

## Output Language

- Report in Chinese (中文)
- Repository names in English
```

### Step 2: 在任务配置中注册

编辑 `config/tasks.yaml`，添加新任务：

```yaml
tasks:
  # ... 已有任务 ...

  # GitHub 星标监控
  star_monitor:
    skill: github_star_monitor        # 对应 .claude/skills/github-star-monitor/
    description: "监控 GitHub 仓库星标增长"
    schedule: "daily 10:00"
    enabled: true
    parameters:
      repos:
        - "anthropics/claude-code"
        - "openai/openai-python"
      report_dir: "reports/github"
```

### Step 3: 验证

```bash
# 确认新 Skill 已被发现
python -m src.cli skills

# 手动测试执行
python -m src.cli -v run star_monitor
```

### Step 4: 注册定时任务

```bash
python -m src.cli schedule add star_monitor --at "daily 10:00"
```

## Skill 开发规范

### SKILL.md 格式

SKILL.md 由两部分组成：

**1. YAML Frontmatter（必须）**

```yaml
---
name: skill-name              # Skill 名称，用于 slash command
description: |                # Skill 描述和触发词
  描述这个 Skill 做什么。
  Triggers: "触发词1", "触发词2"。
---
```

- `name`：使用小写字母 + 连字符，如 `arxiv-tracker`
- `description`：清晰描述功能和触发关键词

**2. Markdown Body**

建议包含以下章节：

```markdown
# Skill 标题

简要说明。

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `param1` | string | `"default"` | 参数说明 |
| `param2` | array | `["a"]` | 数组参数 |
| `param3` | integer | `10` | 数字参数 |

## Workflow

1. **步骤名**: 具体操作描述
2. **步骤名**: 具体操作描述
   ...

## Output Language

输出语言规则。

## Notes (可选)

补充说明、注意事项。
```

### 参数传递规则

`config/tasks.yaml` 中的 `parameters` 会按以下规则拼接到 slash command 中：

| YAML 参数类型 | 拼接结果 | 示例 |
|--------------|---------|------|
| 字符串（无空格） | `key=value` | `max_papers=5` |
| 字符串（有空格） | `key="value with space"` | `query="machine learning"` |
| 数组 | `key=[a,b,c]` | `keywords=[LLM,agent,RL]` |

最终 prompt 格式：`/<skill-name> key1=val1 key2=val2 ...`

### 可用的内置工具

Skill 的 Workflow 中可以使用 Claude 的所有内置能力：

- **WebSearch** - 网络搜索
- **文件读写** - 读写本地文件
- **代码执行** - Bash 命令
- **分析能力** - 数据分析和推理

不需要额外声明工具，SDK 会根据 Skill 的 Workflow 内容自动调用合适的工具。

## 命名约定

| 概念 | 目录名 | slash command | config skill 字段 |
|------|--------|---------------|------------------|
| ArXiv 追踪 | `arxiv-tracker` | `/arxiv-tracker` | `arxiv_tracker` |
| 网页监控 | `web-monitor` | `/web-monitor` | `web_monitor` |
| 每日摘要 | `daily-summary` | `/daily-summary` | `daily_summary` |

规律：目录名用连字符 `-`，config 中用下划线 `_`，系统自动转换。

## 日志

每次任务执行会在 `logs/` 目录下生成日志文件：

```
logs/
├── morning_papers_20260404_080000.txt
├── site_monitor_20260404_090000.txt
└── daily_report_20260404_180000.txt
```

日志内容包括：任务名称、Skill 名称、执行时间、费用、耗时、轮次数、prompt 和完整输出结果。
