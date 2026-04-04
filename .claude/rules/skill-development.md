# Skill 开发规范

## Skill 目录结构

每个 Skill 是 `.claude/skills/` 下的一个子目录：

```
.claude/skills/
└── <skill-name>/          # 使用小写字母 + 连字符
    ├── SKILL.md            # 必须存在，Skill 定义
    └── assets/             # 可选，模板、资源文件
```

## SKILL.md 格式要求

### Frontmatter（必须）

```yaml
---
name: skill-name            # 与目录名一致，小写 + 连字符
description: |              # 清晰描述功能和触发词
  简要描述功能。
  Triggers: "触发词1", "触发词2"。
---
```

### Body 结构（建议）

```markdown
# Skill 标题

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `param1` | type | `default` | 说明 |

## Workflow

1. **步骤名**: 具体操作
2. **步骤名**: 具体操作

## Output Language / Output Format

输出语言和格式规则。
```

## 参数约定

- 参数表格使用 `## Parameters` 标题下的 Markdown 表格
- 四列：`Parameter`、`Type`、`Default`、`Description`
- 参数名用反引号包裹：`` `param_name` ``

## 命名映射

| 概念 | 目录名 / SKILL.md name | config.yaml skill 字段 | slash command |
|------|----------------------|----------------------|---------------|
| 格式 | `lowercase-hyphen` | `lowercase_underscore` | `/lowercase-hyphen` |

系统自动将下划线 `_` 转为连字符 `-`。新 Skill 应保持这一约定。

## 参数传递

`config/tasks.yaml` 的 `parameters` 按以下规则拼接为 slash command：

| 类型 | 拼接格式 | 示例 |
|------|---------|------|
| 字符串（无空格） | `key=value` | `max_papers=5` |
| 字符串（有空格） | `key="spaced value"` | `query="machine learning"` |
| 数组 | `key=[a,b,c]` | `keywords=[LLM,agent]` |

## 工作流编写

- Workflow 步骤用编号列表，每步加粗步骤名
- 步骤应描述 Claude 需要做什么，而非实现细节
- 可引用 `assets/` 下的模板文件
- 明确说明输出语言（中文报告、英文术语保留原文）

## 新增任务流程

1. 在 `.claude/skills/` 下创建 `<skill-name>/SKILL.md`
2. 在 `config/tasks.yaml` 添加任务配置（`skill` 字段对应目录名）
3. 用 `python -m src.cli skills` 验证 Skill 被发现
4. 用 `python -m src.cli run <task_name>` 测试执行
5. 用 `python -m src.cli schedule add <task_name> --at "daily 08:00"` 注册定时

## 质量检查

- SKILL.md 的 frontmatter 必须包含 `name` 和 `description`
- Parameters 表格必须存在且格式正确
- Workflow 至少包含 3 个步骤
- 必须明确 Output Language 规则
