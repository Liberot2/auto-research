"""
核心 Agent 模块 - 封装 Claude Agent SDK 的 query() API

使用 setting_sources=["project", "local"] 自动加载 .claude/skills/ 目录
和 ~/.claude/settings.json 中的环境变量，通过 slash command 触发对应 Skill 执行。
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Agent 执行结果"""

    text: str = ""
    total_cost_usd: float = 0.0
    num_turns: int = 0
    duration_ms: int = 0
    is_error: bool = False
    errors: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    structured_output: Any = None


class Agent:
    """基于 Claude Agent SDK 的 Agent 封装

    通过 setting_sources=["project", "local"] 自动加载：
    - 项目级 .claude/settings.json（Skills 等）
    - 用户级 ~/.claude/settings.json（env 环境变量、认证等）
    使用 bypassPermissions 模式实现无人值守执行。
    """

    def __init__(
        self,
        max_turns: int = 10,
        model: str | None = None,
        cwd: str | Path | None = None,
        max_budget_usd: float | None = None,
    ):
        self.max_turns = max_turns
        self.model = model
        self.cwd = cwd
        self.max_budget_usd = max_budget_usd
        self.stderr_log: list[str] = []

    def _capture_stderr(self, line: str) -> None:
        """捕获 SDK 子进程的 stderr 输出"""
        logger.debug("SDK stderr: %s", line)
        self.stderr_log.append(line)

    def _build_options(self) -> ClaudeAgentOptions:
        """构建 SDK 查询选项"""
        kwargs: dict[str, Any] = {
            "max_turns": self.max_turns,
            "permission_mode": "bypassPermissions",
            "setting_sources": ["project", "local"],
            "stderr": self._capture_stderr,
        }

        if self.model:
            kwargs["model"] = self.model
        if self.cwd:
            kwargs["cwd"] = self.cwd
        if self.max_budget_usd is not None:
            kwargs["max_budget_usd"] = self.max_budget_usd

        return ClaudeAgentOptions(**kwargs)

    async def run(self, prompt: str) -> AgentResponse:
        """执行 agent 查询并收集结果

        Args:
            prompt: slash command 提示词, 如 /arxiv-tracker keywords=[LLM] max_papers=5
        """
        response = AgentResponse()
        options = self._build_options()
        text_parts: list[str] = []

        logger.info("Agent query started, prompt: %s", prompt[:100])

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        response.tool_calls.append({
                            "name": block.name,
                            "input": block.input,
                            "id": block.id,
                        })
                        logger.debug("Tool call: %s", block.name)

            elif isinstance(message, ResultMessage):
                response.total_cost_usd = message.total_cost_usd or 0.0
                response.num_turns = message.num_turns
                response.duration_ms = message.duration_ms
                response.is_error = message.is_error
                if message.errors:
                    response.errors = message.errors
                if message.result:
                    response.text = message.result
                else:
                    response.text = "".join(text_parts)
                if message.structured_output:
                    response.structured_output = message.structured_output

        logger.info(
            "Agent query done, turns=%d, cost=%.4f, duration=%dms",
            response.num_turns,
            response.total_cost_usd,
            response.duration_ms,
        )

        return response
