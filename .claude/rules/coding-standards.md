---
paths:
  - "src/**/*.py"
---

# Python 编码规范

## 类型与语法

- Python >= 3.10：使用 `X | Y` 联合类型，不用 `Union[X, Y]`
- 所有公开函数必须标注参数类型和返回类型
- 使用 `pathlib.Path` 而非 `os.path`
- 使用 `async/await` 进行所有 I/O 操作

## 命名

| 类型 | 风格 | 示例 |
|------|------|------|
| 文件/模块 | `snake_case` | `runner.py`, `windows.py` |
| 类 | `PascalCase` | `TaskRunner`, `AgentResponse` |
| 函数/方法 | `snake_case` | `run_task()`, `load_config()` |
| 私有函数 | `_` 前缀 | `_build_slash_command()` |
| 常量 | `UPPER_SNAKE_CASE` | `TASK_FOLDER` |

## 导入顺序

```python
# 1. 标准库
import logging
from pathlib import Path
from typing import Any

# 2. 第三方库
import yaml
from claude_agent_sdk import query, ClaudeAgentOptions

# 3. 项目内部
from src.core.agent import Agent, AgentResponse
from src.core.runner import TaskRunner
from src.scheduler.windows import create_task_xml
```

## 文档字符串

- 使用三引号 `"""` 格式
- 模块级：简要说明文件职责
- 类级：说明类的用途
- 函数级：说明功能和参数（中文描述）

```python
def run_task(self, task_name: str) -> TaskResult:
    """执行指定任务"""
```

## 错误处理

- 使用 `try/except` + `logging` 记录错误
- 使用 `traceback.format_exc()` 捕获完整堆栈
- 返回 `TaskResult` 或布尔值表示成功/失败，不要静默吞异常

## 日志

- 每个模块开头创建 `logger = logging.getLogger(__name__)`
- 关键操作用 `INFO`，调试信息用 `DEBUG`，错误用 `ERROR`
- 日志消息使用英文（避免 Windows 控制台编码问题）

## 文件编码

- 所有文件读写指定 `encoding="utf-8"`
- Windows 环境下避免在代码中嵌入 emoji 字符（可能导致 GBK 编码错误）

## 禁止事项

- 不要使用 `os.system()` 或 `subprocess` 执行简单文件操作，用 `pathlib`
- 不要引入新的自定义 Skill 加载机制（SDK 原生支持）
- 不要在 `src/` 中硬编码具体任务的业务逻辑（应放在 Skill 中）
- 不要使用 `Union` 类型（用 `X | Y` 替代）
