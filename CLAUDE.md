# Auto Research - Claude Agent SDK 定时任务框架

基于 Claude Agent SDK 的定时任务系统。通过 `.claude/skills/` 下的 Skill 定义任务逻辑，`config/tasks.yaml` 配置调度参数，Windows 任务计划程序触发执行。

## 项目结构

```
src/
  cli.py                      # CLI 入口，提供 run/list/skills/schedule 子命令
  core/
    agent.py                  # Agent 封装，调用 SDK query() API
    runner.py                 # 任务运行器，读取配置 → 构建 slash command → 调用 Agent → 保存日志
  scheduler/
    windows.py                # Windows 任务计划程序集成
.claude/skills/               # Claude Code Skill 定义目录
config/tasks.yaml             # 任务配置（Skill 引用 + 参数 + 时间表）
docs/guide.md                 # 开发指南
```

## 开发命令

```bash
# 安装依赖
.venv/Scripts/pip install -e .

# 语法检查
.venv/Scripts/python -m py_compile src/core/agent.py
.venv/Scripts/python -m py_compile src/core/runner.py
.venv/Scripts/python -m py_compile src/scheduler/windows.py
.venv/Scripts/python -m py_compile src/cli.py

# 验证导入
.venv/Scripts/python -c "from src.core.agent import Agent; from src.core.runner import TaskRunner; print('OK')"

# CLI 测试
.venv/Scripts/python -m src.cli skills
.venv/Scripts/python -m src.cli list

# 运行任务
.venv/Scripts/python -m src.cli run <task_name>
```

## 核心约束

- Python >= 3.10，使用 `X | Y` 联合类型语法，不用 `Union`
- 异步执行：所有 Agent 调用使用 `async/await`，入口通过 `asyncio.run()`
- Skill 是唯一的任务逻辑载体，不要在 `src/` 中硬编码任务逻辑
- 不需要自定义 SkillLoader，SDK 的 `setting_sources` 会自动发现 `.claude/skills/`

## 详细规则

编码规范和架构约束详见 @.claude/rules/coding-standards.md
Skill 开发规范详见 @.claude/rules/skill-development.md
