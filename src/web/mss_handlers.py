"""MSS SOP management web handlers.

Provides routes for viewing captures, managing SOPs, and monitoring executions.
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sanic import Request, Sanic, response

from src.web.mss_templates import (
    render_captures_page,
    render_capture_detail,
    render_executions_page,
    render_execution_detail,
    render_sop_detail,
    render_sops_page,
)

logger = logging.getLogger(__name__)


def register_mss_routes(app: Sanic) -> None:
    """Register MSS SOP management routes."""

    @app.route("/mss/captures")
    async def mss_captures_list(request: Request) -> response.HTTPResponse:
        captures_dir = _get_data_dir(request, "mss_captures")
        captures = _list_captures(captures_dir)
        html = render_captures_page(captures)
        return response.html(html)

    @app.route("/mss/captures/<filename:path>")
    async def mss_capture_detail(request: Request, filename: str) -> response.HTTPResponse:
        captures_dir = _get_data_dir(request, "mss_captures")
        filepath = captures_dir / filename
        if not filepath.exists():
            return response.text("Capture not found", status=404)
        with open(filepath, encoding="utf-8") as f:
            capture = json.load(f)
        html = render_capture_detail(capture, filename)
        return response.html(html)

    @app.route("/api/mss/captures/<filename:path>/generate-sop", methods=["POST"])
    async def mss_generate_sop(request: Request, filename: str) -> response.HTTPResponse:
        """Trigger SOP generation via mss-capture skill."""
        captures_dir = _get_data_dir(request, "mss_captures")
        filepath = captures_dir / filename
        if not filepath.exists():
            return response.json({"error": "Capture not found"}, status=404)

        body = request.json or {}
        sop_name = body.get("sop_name", "")

        # Build slash command for mss-capture skill
        capture_path = str(filepath)
        cmd_parts = [sys.executable, "-m", "src.cli", "run"]
        # We'll use the runner to execute the skill
        # For now, return instruction
        return response.json({
            "message": "SOP generation initiated",
            "capture_file": capture_path,
            "sop_name": sop_name or "(auto)",
            "hint": "Use: /mss-capture capture_file=\"" + capture_path + "\"",
        })

    @app.route("/mss/sops")
    async def mss_sops_list(request: Request) -> response.HTTPResponse:
        sops_dir = _get_sops_dir(request)
        sops = _list_sops(sops_dir)
        html = render_sops_page(sops)
        return response.html(html)

    @app.route("/mss/sops/<name>")
    async def mss_sop_detail(request: Request, name: str) -> response.HTTPResponse:
        sops_dir = _get_sops_dir(request)
        sop_path = _find_sop(sops_dir, name)
        if not sop_path:
            return response.text("SOP not found", status=404)

        with open(sop_path, encoding="utf-8") as f:
            import yaml
            sop = yaml.safe_load(f) or {}

        # Check for execution history
        executions = _list_executions_for_sop(_get_data_dir(request, "mss_executions"), name)

        html = render_sop_detail(sop, name, executions)
        return response.html(html)

    @app.route("/api/mss/sops/<name>/execute", methods=["POST"])
    async def mss_sop_execute(request: Request, name: str) -> response.HTTPResponse:
        """Execute a SOP with given parameters."""
        sops_dir = _get_sops_dir(request)
        sop_path = _find_sop(sops_dir, name)
        if not sop_path:
            return response.json({"error": "SOP not found"}, status=404)

        params = request.json or {}

        try:
            from src.mss.executor import SopExecutor
            executor = SopExecutor(sops_dir=sops_dir)
            result = await executor.run(name, params)

            return response.json({
                "sop_name": result.sop_name,
                "status": result.status,
                "output": result.output,
                "error": result.error,
                "steps": [
                    {
                        "step_id": s.step_id,
                        "step_name": s.step_name,
                        "status": s.status,
                        "http_status": s.http_status,
                        "extracted": s.extracted,
                        "error": s.error,
                        "duration_ms": s.duration_ms,
                    }
                    for s in result.steps
                ],
            })
        except Exception as e:
            logger.error("SOP execution failed: %s", e, exc_info=True)
            return response.json({"error": str(e)}, status=500)

    @app.route("/mss/executions")
    async def mss_executions_list(request: Request) -> response.HTTPResponse:
        executions_dir = _get_data_dir(request, "mss_executions")
        executions = _list_all_executions(executions_dir)
        html = render_executions_page(executions)
        return response.html(html)

    @app.route("/mss/executions/<date>/<filename>")
    async def mss_execution_detail(request: Request, date: str, filename: str) -> response.HTTPResponse:
        executions_dir = _get_data_dir(request, "mss_executions")
        filepath = executions_dir / date / filename
        if not filepath.exists():
            return response.text("Execution not found", status=404)

        with open(filepath, encoding="utf-8") as f:
            execution = json.load(f)
        html = render_execution_detail(execution, date, filename)
        return response.html(html)


def _get_data_dir(request: Request, subdir: str) -> Path:
    """Get data directory path from app context."""
    config_path = getattr(request.app.ctx, "config_path", None)
    if config_path:
        return config_path.parent.parent / "data" / subdir
    return Path("data") / subdir


def _get_sops_dir(request: Request) -> Path:
    """Get SOP definitions directory."""
    config_path = getattr(request.app.ctx, "config_path", None)
    if config_path:
        return config_path.parent / "mss_sops"
    return Path("config/mss_sops")


def _list_captures(captures_dir: Path) -> list[dict[str, Any]]:
    """List capture session files."""
    if not captures_dir.exists():
        return []

    captures: list[dict[str, Any]] = []
    for path in sorted(captures_dir.glob("*.json"), reverse=True):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            captures.append({
                "filename": path.name,
                "session_id": data.get("session_id", path.stem),
                "start_time": data.get("start_time", ""),
                "end_time": data.get("end_time", ""),
                "action_count": data.get("action_count", len(data.get("actions", []))),
                "mss_base_url": data.get("mss_base_url", ""),
            })
        except Exception:
            captures.append({
                "filename": path.name,
                "session_id": path.stem,
                "start_time": "",
                "end_time": "",
                "action_count": 0,
                "mss_base_url": "",
            })
    return captures


def _list_sops(sops_dir: Path) -> list[dict[str, Any]]:
    """List SOP definitions."""
    if not sops_dir.exists():
        return []

    import yaml

    sops: list[dict[str, Any]] = []
    for path in sorted(sops_dir.glob("*.y*ml")):
        if path.name.startswith(".") or path.name == ".gitkeep":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                sop = yaml.safe_load(f) or {}
            steps = sop.get("steps", [])
            required_params = [
                k for k, v in sop.get("input_parameters", {}).items()
                if v.get("required", False)
            ]
            sops.append({
                "name": sop.get("name", path.stem),
                "description": sop.get("description", ""),
                "file": path.name,
                "step_count": len(steps),
                "required_params": required_params,
                "version": sop.get("version", ""),
            })
        except Exception as e:
            sops.append({
                "name": path.stem,
                "description": f"Error: {e}",
                "file": path.name,
                "step_count": 0,
                "required_params": [],
                "version": "",
            })
    return sops


def _find_sop(sops_dir: Path, name: str) -> Path | None:
    """Find a SOP file by name."""
    for ext in [".yaml", ".yml"]:
        path = sops_dir / f"{name}{ext}"
        if path.exists():
            return path
    # Also try matching by filename stem
    for path in sops_dir.glob("*.y*ml"):
        if path.stem == name:
            return path
    return None


def _list_all_executions(executions_dir: Path) -> list[dict[str, Any]]:
    """List all execution records."""
    if not executions_dir.exists():
        return []

    executions: list[dict[str, Any]] = []
    for date_dir in sorted(executions_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for filepath in sorted(date_dir.glob("*.json"), reverse=True):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                executions.append({
                    "sop_name": data.get("sop_name", ""),
                    "status": data.get("status", ""),
                    "started_at": data.get("started_at", ""),
                    "finished_at": data.get("finished_at", ""),
                    "date": date_dir.name,
                    "filename": filepath.name,
                    "step_count": len(data.get("steps", [])),
                })
            except Exception:
                pass
    return executions


def _list_executions_for_sop(executions_dir: Path, sop_name: str) -> list[dict[str, Any]]:
    """List execution records for a specific SOP."""
    if not executions_dir.exists():
        return []

    executions: list[dict[str, Any]] = []
    for date_dir in sorted(executions_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for filepath in sorted(date_dir.glob(f"{sop_name}_*.json"), reverse=True):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                executions.append({
                    "status": data.get("status", ""),
                    "started_at": data.get("started_at", ""),
                    "finished_at": data.get("finished_at", ""),
                    "date": date_dir.name,
                    "filename": filepath.name,
                    "error": data.get("error"),
                })
            except Exception:
                pass
    return executions
