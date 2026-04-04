# 架构约束

## 核心原则

- **Skill 是唯一的任务逻辑载体** — 具体的业务逻辑（搜索论文、监控网页等）全部定义在 `.claude/skills/` 的 SKILL.md 中，`src/` 只负责调度和执行框架
- **不要重复造轮子** — SDK 原生支持 Skill 加载（`setting_sources`）、slash command 匹配，不需要自定义 SkillLoader、参数解析器等
- **保持 src/ 精简** — `src/` 只包含调度框架代码（agent、runner、cli、windows_task），不应该膨胀

## 执行流程（不要修改）

```
Windows Scheduler → CLI → TaskRunner → Agent → SDK query() → Skill → Log
```

关键路径：
1. `CLI` 调用 `TaskRunner.load_config()` 读取 `config/tasks.yaml`
2. `TaskRunner.run_task()` 用 `_build_slash_command()` 构建 prompt
3. `Agent.run()` 调用 SDK `query(prompt, options)`
4. SDK 自动匹配 Skill 并执行 Workflow
5. 结果写入 `logs/` 目录

## Agent 配置

Agent 构造参数固定为：

```python
ClaudeAgentOptions(
    max_turns=10,
    permission_mode="bypassPermissions",
    setting_sources=["project", "local"],
)
```

- `setting_sources=["project", "local"]` — 自动加载 `.claude/skills/`
- `permission_mode="bypassPermissions"` — 无人值守模式
- 不要添加 `system_prompt`、`tools`、`mcp_servers` 等参数（Skill 自带工具定义）

## 配置格式

`config/tasks.yaml` 结构：

```yaml
log_dir: logs

tasks:
  <task_name>:                    # 自定义任务名
    skill: <skill_name>           # .claude/skills/ 下的目录名
    description: "任务描述"
    schedule: "daily HH:MM"       # 时间表
    enabled: true/false
    parameters:                   # 传递给 slash command 的参数
      key: value
```

- `skill` 字段使用下划线 `_`，系统自动转为连字符 `-` 匹配 slash command
- `parameters` 会被拼接到 slash command 中，不要添加 `timestamp`/`date`/`task_name` 键（系统自动注入）

## 命名映射

| 概念 | 目录名 | slash command | config skill 字段 |
|------|--------|---------------|------------------|
| ArXiv 追踪 | `arxiv-tracker` | `/arxiv-tracker` | `arxiv_tracker` |

规律：目录名和 slash command 用连字符 `-`，config 中用下划线 `_`。

## 扩展方式

需要新功能时：
- **新任务类型** → 创建新的 `.claude/skills/<name>/SKILL.md` + 在 `config/tasks.yaml` 添加配置
- **新 CLI 命令** → 在 `src/cli.py` 添加子命令
- **新调度方式** → 在 `src/windows_task.py` 添加触发器格式支持

不要：
- 在 `src/` 中添加任务特定的业务逻辑
- 创建新的 Skill 加载/解析机制
- 修改 Agent 的核心执行逻辑（`setting_sources`、`permission_mode`）
