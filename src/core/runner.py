"""
任务运行器 - 基于 Claude Code Skill 的定时任务执行引擎

通过 slash command 触发 .claude/skills/ 下的 Skill 执行。
不需要自定义 SkillLoader，SDK 的 setting_sources 会自动发现 Skills。
"""

import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from src.core.agent import Agent, AgentResponse

logger = logging.getLogger(__name__)


class TaskContext:
    """任务执行上下文"""

    def __init__(self, task_name: str, config: dict[str, Any], log_dir: Path):
        self.task_name = task_name
        self.config = config
        self.log_dir = log_dir
        self.timestamp = datetime.now()

    def get_log_path(self, suffix: str = ".log") -> Path:
        date_dir = self.log_dir / self.timestamp.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.task_name}_{self.timestamp.strftime('%H%M%S')}{suffix}"
        return date_dir / filename


class TaskResult:
    """任务执行结果"""

    def __init__(
        self,
        task_name: str,
        success: bool,
        response: AgentResponse | None = None,
        error: str | None = None,
    ):
        self.task_name = task_name
        self.success = success
        self.response = response
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "task_name": self.task_name,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.response:
            result["cost_usd"] = self.response.total_cost_usd
            result["duration_ms"] = self.response.duration_ms
            result["num_turns"] = self.response.num_turns
            result["text"] = self.response.text[:500] if self.response.text else ""
        if self.error:
            result["error"] = self.error
        return result

    def __repr__(self) -> str:
        status = "成功" if self.success else f"失败({self.error})"
        return f"TaskResult({self.task_name}, {status})"


def _build_slash_command(skill_name: str, params: dict[str, Any]) -> str:
    """根据 skill 名称和参数构建 slash command

    例如: /arxiv-tracker keywords=["LLM","agent"] max_papers=5
    """
    cmd_name = "/" + skill_name.replace("_", "-")

    args_parts = []
    for key, value in params.items():
        # 跳过内部参数
        if key in ("timestamp", "date", "task_name"):
            continue
        if isinstance(value, list):
            formatted_list = ",".join(str(v) for v in value)
            args_parts.append(f'{key}=[{formatted_list}]')
        elif isinstance(value, str) and " " in value:
            args_parts.append(f'{key}="{value}"')
        else:
            args_parts.append(f"{key}={value}")

    if args_parts:
        return f"{cmd_name} {' '.join(args_parts)}"
    return cmd_name


class TaskRunner:
    """基于 Claude Code Skill 的任务运行器"""

    def __init__(self, config_path: str | Path = "config/tasks.yaml"):
        self.config_path = Path(config_path)
        self.tasks_config: dict[str, dict[str, Any]] = {}
        self.log_dir = Path("logs")

    def load_config(self) -> None:
        """从 YAML 加载任务配置"""
        if not self.config_path.exists():
            logger.warning("配置文件不存在: %s", self.config_path)
            return

        with open(self.config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        self.tasks_config = config.get("tasks", {})
        log_dir = config.get("log_dir", "logs")
        self.log_dir = Path(log_dir)
        if not self.log_dir.is_absolute():
            self.log_dir = self.config_path.parent.parent / log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info("加载了 %d 个任务配置", len(self.tasks_config))

    async def run_task(self, task_name: str, max_retries: int = 1) -> TaskResult:
        """执行指定任务，失败后自动重试"""
        if task_name not in self.tasks_config:
            raise ValueError(f"未找到任务配置: {task_name}")

        task_config = self.tasks_config[task_name]
        skill_name = task_config.get("skill")
        if not skill_name:
            raise ValueError(f"任务 '{task_name}' 缺少 skill 字段")

        last_result: TaskResult | None = None
        for attempt in range(max_retries + 1):
            result = await self._execute_task(task_name, task_config, skill_name)
            if result.success:
                return result
            last_result = result
            if attempt < max_retries:
                logger.warning(
                    "Task %s failed (attempt %d/%d), retrying in 30s...",
                    task_name, attempt + 1, max_retries + 1,
                )
                await asyncio.sleep(30)

        return last_result  # type: ignore[return-value]

    async def _execute_task(
        self, task_name: str, task_config: dict[str, Any], skill_name: str
    ) -> TaskResult:
        """单次执行任务"""

        context = TaskContext(
            task_name=task_name,
            config=task_config,
            log_dir=self.log_dir,
        )

        logger.info("开始执行任务: %s (skill: %s)", task_name, skill_name)
        try:
            # 合并参数
            params = dict(task_config.get("parameters", {}))
            params["timestamp"] = context.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            params["date"] = context.timestamp.strftime("%Y-%m-%d")
            params["task_name"] = task_name
            params["report_path"] = str(context.get_log_path("_report.md"))

            # 构建 slash command prompt
            prompt = _build_slash_command(skill_name, params)
            logger.info("Slash command: %s", prompt)

            # 创建 Agent 并执行
            project_dir = str(self.config_path.parent.parent.resolve())
            agent = Agent(
                max_turns=task_config.get("max_turns", 10),
                cwd=project_dir,
            )
            response = await agent.run(prompt)

            # 保存结果日志
            log_path = context.get_log_path(".txt")
            log_path.write_text(
                f"Task: {task_name}\n"
                f"Skill: {skill_name}\n"
                f"Time: {context.timestamp.isoformat()}\n"
                f"Success: True\n"
                f"Cost: ${response.total_cost_usd:.4f}\n"
                f"Duration: {response.duration_ms}ms\n"
                f"Turns: {response.num_turns}\n"
                f"\n--- Prompt ---\n{prompt}\n"
                f"\n--- Result ---\n{response.text}\n",
                encoding="utf-8",
            )

            return TaskResult(
                task_name=task_name,
                success=True,
                response=response,
            )
        except Exception:
            error_msg = traceback.format_exc()
            logger.error("Task %s failed: %s", task_name, error_msg)
            # Always write execution log, even on failure
            log_path = context.get_log_path(".txt")
            log_path.write_text(
                f"Task: {task_name}\n"
                f"Skill: {skill_name}\n"
                f"Time: {context.timestamp.isoformat()}\n"
                f"Success: False\n"
                f"\n--- Prompt ---\n{prompt}\n"
                f"\n--- Error ---\n{error_msg}\n",
                encoding="utf-8",
            )
            # Save captured stderr for debugging
            if agent.stderr_log:
                stderr_path = context.get_log_path("_stderr.txt")
                stderr_path.write_text(
                    "\n".join(agent.stderr_log),
                    encoding="utf-8",
                )
                logger.error("SDK stderr saved to: %s", stderr_path)
            return TaskResult(
                task_name=task_name,
                success=False,
                error=error_msg,
            )

    async def run_all(self) -> list[TaskResult]:
        """执行所有已启用的任务"""
        results = []
        for task_name, task_config in self.tasks_config.items():
            if not task_config.get("enabled", True):
                logger.info("跳过已禁用的任务: %s", task_name)
                continue
            result = await self.run_task(task_name)
            results.append(result)
        return results

    def list_tasks(self) -> list[dict[str, Any]]:
        """列出所有已配置的任务"""
        tasks = []
        for name, config in self.tasks_config.items():
            skill_name = config.get("skill", "unknown")
            tasks.append({
                "name": name,
                "skill": skill_name,
                "description": config.get("description", ""),
                "enabled": config.get("enabled", True),
            })
        return tasks

    def list_skills(self) -> list[dict[str, str]]:
        """列出所有可用的 Claude Code Skills"""
        skills_dir = self.config_path.parent.parent / ".claude" / "skills"
        if not skills_dir.exists():
            return []
        return [
            {"name": d.name}
            for d in sorted(skills_dir.iterdir())
            if d.is_dir()
            and (d / "SKILL.md").exists()
            and not d.name.startswith(("_", "."))
        ]
