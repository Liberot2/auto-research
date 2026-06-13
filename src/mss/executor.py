"""SOP execution engine for MSS platform automation.

Loads SOP YAML definitions, resolves parameters, executes API calls step-by-step,
handles conditions, retry, approval gates, and variable extraction.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.mss.auth import AuthManager
from src.mss.substitution import (
    evaluate_condition,
    extract_variables,
    resolve_templates,
)

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_SOPS_DIR = Path("config/mss_sops")
DEFAULT_AUTH_PATH = Path("config/mss_auth.yaml")
DEFAULT_EXECUTIONS_DIR = Path("data/mss_executions")


@dataclass
class StepResult:
    """Result of a single SOP step execution."""

    step_id: str
    step_name: str
    method: str
    path: str
    status: str  # "success", "skipped", "failed", "awaiting_approval", "approved", "rejected"
    http_status: int | None = None
    extracted: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: int | None = None
    step_type: str = "api"  # "api" | "approval"
    retry_count: int = 0
    # Approval-specific fields
    approver: str | None = None
    decision_time: str | None = None
    notification_sent: str | None = None


@dataclass
class SopResult:
    """Result of a complete SOP execution."""

    sop_name: str
    status: str  # "success", "failed", "partial"
    started_at: str = ""
    finished_at: str = ""
    steps: list[StepResult] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class SopExecutor:
    """Executes SOP definitions against the MSS platform API."""

    def __init__(
        self,
        sops_dir: Path | None = None,
        auth_path: Path | None = None,
        executions_dir: Path | None = None,
    ) -> None:
        self._sops_dir = sops_dir or DEFAULT_SOPS_DIR
        self._auth = AuthManager(auth_path or DEFAULT_AUTH_PATH)
        self._executions_dir = executions_dir or DEFAULT_EXECUTIONS_DIR

    def load_sop(self, sop_name: str) -> dict[str, Any]:
        """Load and parse a SOP YAML file."""
        sop_path = self._sops_dir / f"{sop_name}.yaml"
        if not sop_path.exists():
            # Also try .yml extension
            sop_path = self._sops_dir / f"{sop_name}.yml"
        if not sop_path.exists():
            raise FileNotFoundError(f"SOP not found: {sop_name} (searched in {self._sops_dir})")

        with open(sop_path, encoding="utf-8") as f:
            sop = yaml.safe_load(f)

        if not sop or "steps" not in sop:
            raise ValueError(f"Invalid SOP: missing 'steps' in {sop_name}")

        logger.info("Loaded SOP '%s' with %d steps", sop_name, len(sop["steps"]))
        return sop

    def validate_inputs(self, sop: dict[str, Any], params: dict[str, Any]) -> list[str]:
        """Validate that all required input parameters are provided.

        Returns list of missing parameter names (empty if all valid).
        """
        missing: list[str] = []
        input_params = sop.get("input_parameters", {})
        for name, schema in input_params.items():
            if schema.get("required", False) and name not in params:
                # Check if there's a default
                if "default" not in schema:
                    missing.append(name)
        return missing

    def list_sops(self) -> list[dict[str, str]]:
        """List all available SOP definitions."""
        if not self._sops_dir.exists():
            return []

        results: list[dict[str, str]] = []
        for path in sorted(self._sops_dir.glob("*.y*ml")):
            if path.name.startswith("."):
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    sop = yaml.safe_load(f) or {}
                results.append({
                    "name": sop.get("name", path.stem),
                    "description": sop.get("description", ""),
                    "file": path.name,
                })
            except Exception as e:
                logger.warning("Failed to read SOP %s: %s", path.name, e)
        return results

    async def run(self, sop_name: str, params: dict[str, Any] | None = None) -> SopResult:
        """Execute a complete SOP definition.

        Args:
            sop_name: Name of the SOP (without extension).
            params: Input parameters for template substitution.

        Returns:
            SopResult with step-by-step execution details.
        """
        params = params or {}
        sop = self.load_sop(sop_name)

        # Validate inputs
        missing = self.validate_inputs(sop, params)
        if missing:
            return SopResult(
                sop_name=sop_name,
                status="failed",
                error=f"Missing required parameters: {', '.join(missing)}",
            )

        # Fill defaults for optional params
        input_params = sop.get("input_parameters", {})
        for name, schema in input_params.items():
            if name not in params and "default" in schema:
                params[name] = schema["default"]

        # Get auth token
        auth_config = sop.get("auth", {})
        profile_name = auth_config.get("profile", "")
        base_url = sop.get("base_url", "")

        context: dict[str, Any] = dict(params)

        if profile_name:
            try:
                token = await self._auth.get_token(profile_name)
                context["session_token"] = token
            except Exception as e:
                return SopResult(
                    sop_name=sop_name,
                    status="failed",
                    error=f"Authentication failed: {e}",
                )

        # Execute steps
        result = SopResult(
            sop_name=sop_name,
            status="success",
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        import time

        for step in sop["steps"]:
            step_type = step.get("type", "api")

            # Handle approval steps
            if step_type == "approval":
                step_result = self._handle_approval(step, context, result)
                result.steps.append(step_result)

                if step_result.status == "awaiting_approval":
                    # Save state and pause execution
                    result.status = "awaiting_approval"
                    result.finished_at = datetime.now(timezone.utc).isoformat()
                    self._save_execution(result)
                    return result

                if step_result.status == "rejected":
                    # Jump to on_reject step if defined
                    reject_step_id = step.get("on_reject")
                    if reject_step_id:
                        reject_step = self._find_step(sop, reject_step_id)
                        if reject_step:
                            step_result = await self._execute_step(reject_step, context, base_url, profile_name)
                            result.steps.append(step_result)
                            context.update(step_result.extracted)
                    result.status = "partial"
                    break

                # Approved: record and continue
                context.update(step_result.extracted)
                continue

            # Normal API step
            step_result = await self._execute_step(step, context, base_url, profile_name)
            result.steps.append(step_result)

            # Merge extracted variables into context
            context.update(step_result.extracted)

        result.finished_at = datetime.now(timezone.utc).isoformat()
        result.context = context

        # Build output
        output_config = sop.get("output", {})
        if output_config:
            summary_template = output_config.get("summary", "")
            if summary_template:
                result.output["summary"] = resolve_templates(summary_template, context)
            result.output["fields"] = {
                f: context.get(f, f"<{f} not found>")
                for f in output_config.get("fields", [])
            }

        # Save execution record
        self._save_execution(result)

        return result

    async def _execute_step(
        self,
        step: dict[str, Any],
        context: dict[str, Any],
        base_url: str,
        profile_name: str,
    ) -> StepResult:
        """Execute a single SOP step with retry support."""
        import asyncio
        import httpx
        import time as _time

        step_id = step.get("id", "unknown")
        step_name = step.get("name", step_id)

        # Check condition
        condition = step.get("condition")
        if condition:
            if not evaluate_condition(condition, context):
                logger.info("Step '%s' skipped (condition false: %s)", step_id, condition)
                return StepResult(
                    step_id=step_id,
                    step_name=step_name,
                    method=step.get("method", "GET"),
                    path=step.get("path", ""),
                    status="skipped",
                )

        # Resolve templates
        path = resolve_templates(step.get("path", ""), context)
        headers = resolve_templates(step.get("headers", {}), context)
        body = resolve_templates(step.get("body"), context) if "body" in step else None
        query = resolve_templates(step.get("query_params", {}), context)

        url = f"{base_url}{path}"

        # Add auth header
        if profile_name and not any("authorization" in k.lower() for k in headers):
            try:
                token = context.get("session_token", "")
                auth_header = self._auth.build_auth_header(profile_name, token)
                headers.update(auth_header)
            except Exception:
                pass

        # Get verify_ssl from auth profile
        verify_ssl = True
        if profile_name:
            try:
                profile = self._auth.get_profile(profile_name)
                verify_ssl = profile.get("verify_ssl", True)
            except Exception:
                pass

        # Retry configuration
        retry_config = step.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 1)
        backoff = retry_config.get("backoff_seconds", [1])
        retry_on = retry_config.get("retry_on", [])

        logger.info("Step '%s': %s %s (max_attempts=%d)", step_id, step.get("method", "GET"), path, max_attempts)

        last_error: str | None = None
        for attempt in range(max_attempts):
            start_time = _time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=60, verify=verify_ssl) as client:
                    response = await client.request(
                        method=step.get("method", "GET"),
                        url=url,
                        headers=headers,
                        json=body if body is not None else None,
                        params=query or None,
                    )
                duration_ms = int((_time.monotonic() - start_time) * 1000)

                # Validate response
                expected_status = step.get("expect", {}).get("status")
                if expected_status and response.status_code != expected_status:
                    error_msg = f"Expected status {expected_status}, got {response.status_code}: {response.text[:500]}"
                    if self._should_retry(response.status_code, retry_on) and attempt < max_attempts - 1:
                        logger.warning("Step '%s' attempt %d failed: %s, retrying...", step_id, attempt + 1, error_msg)
                        await asyncio.sleep(backoff[min(attempt, len(backoff) - 1)])
                        last_error = error_msg
                        continue
                    return StepResult(
                        step_id=step_id,
                        step_name=step_name,
                        method=step.get("method", "GET"),
                        path=path,
                        status="failed",
                        http_status=response.status_code,
                        duration_ms=duration_ms,
                        error=error_msg,
                        retry_count=attempt,
                    )

                # Extract variables
                extracted: dict[str, Any] = {}
                extract_config = step.get("extract", {})
                if extract_config:
                    try:
                        response_data = response.json()
                        extracted = extract_variables(response_data, extract_config)
                        logger.info("Extracted: %s", extracted)
                    except Exception as e:
                        logger.warning("Failed to extract variables: %s", e)

                return StepResult(
                    step_id=step_id,
                    step_name=step_name,
                    method=step.get("method", "GET"),
                    path=path,
                    status="success",
                    http_status=response.status_code,
                    extracted=extracted,
                    duration_ms=duration_ms,
                    retry_count=attempt,
                )

            except Exception as e:
                duration_ms = int((_time.monotonic() - start_time) * 1000)
                last_error = str(e)
                if attempt < max_attempts - 1:
                    logger.warning("Step '%s' attempt %d error: %s, retrying...", step_id, attempt + 1, e)
                    await asyncio.sleep(backoff[min(attempt, len(backoff) - 1)])
                    continue

        # All retries exhausted
        logger.error("Step '%s' failed after %d attempts: %s", step_id, max_attempts, last_error)
        return StepResult(
            step_id=step_id,
            step_name=step_name,
            method=step.get("method", "GET"),
            path=path,
            status="failed",
            error=last_error or "Unknown error",
            retry_count=max_attempts,
        )

    @staticmethod
    def _should_retry(status_code: int, retry_on: list[str]) -> bool:
        """Check if a failed request should be retried."""
        if not retry_on:
            return False
        if "timeout" in retry_on and status_code == 0:
            return True
        if "5xx" in retry_on and 500 <= status_code < 600:
            return True
        if "429" in retry_on and status_code == 429:
            return True
        if str(status_code) in retry_on:
            return True
        return False

    @staticmethod
    def _find_step(sop: dict[str, Any], step_id: str) -> dict[str, Any] | None:
        """Find a step by id in the SOP definition."""
        for step in sop.get("steps", []):
            if step.get("id") == step_id:
                return step
        return None

    def _handle_approval(
        self,
        step: dict[str, Any],
        context: dict[str, Any],
        result: "SopResult",
    ) -> StepResult:
        """Handle an approval step - send notification and return awaiting state."""
        step_id = step.get("id", "unknown")
        step_name = step.get("name", step_id)
        notify_config = step.get("notify", {})

        # Send notification if configured
        notification_sent = None
        if notify_config:
            notification_sent = datetime.now(timezone.utc).isoformat()
            self._send_notification(step, context, notify_config, result)

        logger.info("Step '%s' awaiting approval", step_id)

        return StepResult(
            step_id=step_id,
            step_name=step_name,
            method="",
            path="",
            status="awaiting_approval",
            step_type="approval",
            notification_sent=notification_sent,
        )

    def _send_notification(
        self,
        step: dict[str, Any],
        context: dict[str, Any],
        notify_config: dict[str, Any],
        result: "SopResult",
    ) -> None:
        """Send approval notification via webhook."""
        import httpx

        notify_type = notify_config.get("type", "webhook")
        target = notify_config.get("target", "")
        message_template = notify_config.get("message", "Approval required for SOP step")

        if notify_type == "webhook" and target:
            message = resolve_templates(message_template, context)
            try:
                # Support both plain text and markdown (for enterprise WeChat/DingTalk)
                payload: dict[str, Any]
                if "qyapi.weixin.qq.com" in target:
                    # Enterprise WeChat format
                    payload = {
                        "msgtype": "markdown",
                        "markdown": {"content": f"## MSS SOP 审批请求\n> {message}"},
                    }
                elif "oapi.dingtalk.com" in target:
                    # DingTalk format
                    payload = {
                        "msgtype": "markdown",
                        "markdown": {
                            "title": "MSS SOP Approval",
                            "text": f"## MSS SOP 审批请求\n{message}",
                        },
                    }
                else:
                    payload = {"text": message}

                # Fire and forget (sync, non-blocking in practice for short webhook calls)
                httpx.post(target, json=payload, timeout=10)
                logger.info("Notification sent to %s", target)
            except Exception as e:
                logger.warning("Failed to send notification: %s", e)

    def _save_execution(self, result: SopResult) -> None:
        """Save execution record to JSON file."""
        self._executions_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        date_dir = self._executions_dir / now.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{result.sop_name}_{now.strftime('%H%M%S')}.json"
        filepath = date_dir / filename

        # Serialize result
        data = {
            "sop_name": result.sop_name,
            "status": result.status,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "error": result.error,
            "output": result.output,
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "method": s.method,
                    "path": s.path,
                    "status": s.status,
                    "http_status": s.http_status,
                    "extracted": s.extracted,
                    "error": s.error,
                    "duration_ms": s.duration_ms,
                }
                for s in result.steps
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("Execution record saved: %s", filepath)
