"""HTTP request handlers for the report viewer web service"""

import asyncio
import difflib
import json
import logging
import re
import subprocess as sp
import sys
from pathlib import Path

import mistune
from sanic import Sanic
from sanic.request import Request
from sanic.response import html, json as json_resp, text as text_resp

from src.web.report_reader import ReportReader
from src.web.log_reader import LogReader, LogEntry
from src.web.bookmark_store import BookmarkStore
from src.web import templates

logger = logging.getLogger(__name__)

_md = mistune.create_markdown(plugins=["table", "strikethrough", "task_lists"])


def _reader(request: Request) -> ReportReader:
    return request.app.ctx.reader


def _log_reader(request: Request) -> LogReader:
    return request.app.ctx.log_reader


def _bookmark_store(request: Request) -> BookmarkStore:
    return request.app.ctx.bookmark_store


def _task_runner(request: Request):
    return getattr(request.app.ctx, "task_runner", None)


def _rag_service(request: Request):
    return getattr(request.app.ctx, "rag_service", None)


def _meta_to_dict(meta) -> dict:
    return {
        "date": meta.date,
        "task_name": meta.task_name,
        "time_str": meta.time_str,
        "display_time": meta.display_time,
        "filename": meta.filename,
    }


def _date_counts(reader: ReportReader, dates: list[str]) -> dict[str, int]:
    """Build date -> report count mapping"""
    return {d: len(reader.list_reports(d)) for d in dates}


def register_routes(app: Sanic) -> None:
    """Register all routes on the Sanic app"""

    # --- Existing report viewer routes ---

    @app.route("/")
    async def index(request: Request):
        reader = _reader(request)
        dates = reader.list_dates()
        if not dates:
            return html(templates.render_error(dates, "No reports found"))
        latest = dates[0]
        reports = reader.list_reports(latest)
        counts = _date_counts(reader, dates)
        return html(
            templates.render_index(
                dates, latest, [_meta_to_dict(r) for r in reports], date_counts=counts
            )
        )

    @app.route("/date/<date:str>")
    async def show_date(request: Request, date: str):
        reader = _reader(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)
        if date not in dates:
            return html(
                templates.render_error(dates, f"Date not found: {date}", date_counts=counts)
            )
        task_type = request.args.get("task_type", "")
        task_types = reader.list_task_types()
        reports = reader.list_reports(date, task_type=task_type or None)
        return html(
            templates.render_date(
                dates,
                date,
                [_meta_to_dict(r) for r in reports],
                task_types,
                current_type=task_type,
                date_counts=counts,
            )
        )

    @app.route("/report/<date:str>/<filename:str>")
    async def show_report(request: Request, date: str, filename: str):
        reader = _reader(request)
        log_reader = _log_reader(request)
        bm_store = _bookmark_store(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)
        meta = reader.get_report_meta(date, filename)
        if not meta:
            return html(
                templates.render_error(
                    dates, f"Report not found: {date}/{filename}", date_counts=counts
                )
            )
        try:
            content = reader.read_report(date, filename)
        except FileNotFoundError:
            return html(
                templates.render_error(
                    dates, f"Report not found: {date}/{filename}", date_counts=counts
                )
            )
        html_content = _md(content)
        title = f"{meta.task_name} - {meta.display_time}"
        bookmarked = bm_store.is_bookmarked(date, filename)
        return html(
            templates.render_report(
                dates, date, filename, title, html_content,
                date_counts=counts, bookmarked=bookmarked,
            )
        )

    @app.route("/search")
    async def search(request: Request):
        reader = _reader(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)
        query = request.args.get("q", "")
        task_type = request.args.get("task_type", "")
        date = request.args.get("date", "")
        results = []
        if query:
            results = reader.search_reports(
                query,
                task_type=task_type or None,
                date=date or None,
            )
        return html(
            templates.render_search(
                dates,
                query=query,
                task_types=reader.list_task_types(),
                current_type=task_type,
                current_date=date,
                results=[_meta_to_dict(r) for r in results],
                date_counts=counts,
            )
        )

    # --- Task management pages ---

    @app.route("/tasks")
    async def task_list(request: Request):
        reader = _reader(request)
        log_reader = _log_reader(request)
        runner = _task_runner(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)

        if not runner:
            return html(
                templates.render_error(dates, "Task management unavailable (no config)", date_counts=counts)
            )

        tasks = runner.list_tasks()
        for t in tasks:
            t["last_log"] = log_reader.get_latest_for_task(t["name"])

        return html(
            templates.render_task_list(dates, tasks, date_counts=counts)
        )

    @app.route("/tasks/<task_name:str>")
    async def task_detail(request: Request, task_name: str):
        reader = _reader(request)
        log_reader = _log_reader(request)
        runner = _task_runner(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)

        if not runner or task_name not in runner.tasks_config:
            return html(
                templates.render_error(dates, f"Task not found: {task_name}", date_counts=counts)
            )

        task_config = runner.tasks_config[task_name]
        history = log_reader.get_history_for_task(task_name)

        return html(
            templates.render_task_detail(
                dates, task_name, task_config, history, date_counts=counts
            )
        )

    # --- Log viewer ---

    @app.route("/logs/<date:str>/<filename:str>")
    async def show_log(request: Request, date: str, filename: str):
        reader = _reader(request)
        log_reader = _log_reader(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)

        entry = log_reader.parse_log(date, filename)
        if not entry:
            return html(
                templates.render_error(dates, f"Log not found: {date}/{filename}", date_counts=counts)
            )

        return html(
            templates.render_log(dates, entry, date_counts=counts)
        )

    # --- Task action APIs ---

    @app.route("/api/tasks/<task_name:str>/run", methods=["POST"])
    async def api_run_task(request: Request, task_name: str):
        runner = _task_runner(request)
        if not runner:
            return json_resp({"error": "Task runner not available"}, status=503)
        if task_name not in runner.tasks_config:
            return json_resp({"error": f"Task not found: {task_name}"}, status=404)

        # Reload config to ensure latest state
        runner.load_config()

        config_path = getattr(request.app.ctx, "config_path", None)

        def _run():
            try:
                venv_python = str(Path(sys.executable).resolve())
                cmd = [venv_python, "-m", "src.cli", "-c", str(config_path), "run", task_name]
                logger.info("Launching task via subprocess: %s", " ".join(cmd))
                proc = sp.Popen(
                    cmd,
                    cwd=str(Path(__file__).parent.parent.parent),
                    stdout=sp.PIPE,
                    stderr=sp.PIPE,
                )
                stdout, stderr = proc.communicate(timeout=600)
                if proc.returncode == 0:
                    logger.info("Task %s completed (exit 0)", task_name)
                else:
                    logger.error(
                        "Task %s failed (exit %d): %s",
                        task_name,
                        proc.returncode,
                        stderr.decode("utf-8", errors="replace")[:500],
                    )
            except Exception:
                logger.error("Task %s subprocess failed", task_name, exc_info=True)

        asyncio.create_task(asyncio.to_thread(_run))
        return json_resp({"status": "started", "task": task_name})

    @app.route("/api/tasks/<task_name:str>/toggle", methods=["POST"])
    async def api_toggle_task(request: Request, task_name: str):
        runner = _task_runner(request)
        config_path = getattr(request.app.ctx, "config_path", None)
        if not runner or not config_path:
            return json_resp({"error": "Task runner not available"}, status=503)
        if task_name not in runner.tasks_config:
            return json_resp({"error": f"Task not found: {task_name}"}, status=404)

        # Toggle in memory
        current = runner.tasks_config[task_name].get("enabled", True)
        new_val = not current
        runner.tasks_config[task_name]["enabled"] = new_val

        # Update YAML file with regex to preserve comments
        try:
            content = config_path.read_text(encoding="utf-8")
            # Find the task block and toggle enabled
            pattern = re.compile(
                rf"(^  {re.escape(task_name)}:.*?enabled:\s*)\w+",
                re.MULTILINE | re.DOTALL,
            )
            if pattern.search(content):
                content = pattern.sub(
                    lambda m: m.group(1) + str(new_val).lower(),
                    content,
                )
                config_path.write_text(content, encoding="utf-8")
            else:
                return json_resp({"error": "Failed to update config file"}, status=500)
        except Exception as e:
            logger.error("Failed to toggle task: %s", e)
            return json_resp({"error": str(e)}, status=500)

        return json_resp({"task": task_name, "enabled": new_val})

    # --- Report enhancement APIs ---

    @app.route("/api/reports/<date:str>/<filename:str>")
    async def api_report_content(request: Request, date: str, filename: str):
        reader = _reader(request)
        meta = reader.get_report_meta(date, filename)
        if not meta:
            return json_resp({"error": "Report not found"}, status=404)
        try:
            content = reader.read_report(date, filename)
        except FileNotFoundError:
            return json_resp({"error": "Report not found"}, status=404)
        return json_resp({
            "meta": _meta_to_dict(meta),
            "content": content,
        })

    @app.route("/api/reports/<date:str>/<filename:str>/download")
    async def api_download_report(request: Request, date: str, filename: str):
        reader = _reader(request)
        try:
            content = reader.read_report(date, filename)
        except FileNotFoundError:
            return json_resp({"error": "Report not found"}, status=404)
        resp = text_resp(content, content_type="text/markdown; charset=utf-8")
        resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    # --- Report comparison ---

    @app.route("/compare")
    async def compare_page(request: Request):
        reader = _reader(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)
        task_types = reader.list_task_types()

        current_task = request.args.get("task_type", "")
        left_date = request.args.get("left_date", "")
        left_file = request.args.get("left_file", "")
        right_date = request.args.get("right_date", "")
        right_file = request.args.get("right_file", "")

        # Build filtered date/file lists for selectors
        left_dates = dates
        left_files = []
        right_dates = dates
        right_files = []

        if current_task:
            # Only show dates that have reports for this task type
            task_dates = []
            for d in dates:
                reports = reader.list_reports(d, task_type=current_task)
                if reports:
                    task_dates.append(d)
                    if d == left_date:
                        left_files = [_meta_to_dict(r) for r in reports]
                    if d == right_date:
                        right_files = [_meta_to_dict(r) for r in reports]
            left_dates = task_dates
            right_dates = task_dates

        diff_html = ""
        if left_date and left_file and right_date and right_file:
            try:
                left_content = reader.read_report(left_date, left_file)
                right_content = reader.read_report(right_date, right_file)

                left_lines = left_content.splitlines()
                right_lines = right_content.splitlines()

                diff = list(difflib.unified_diff(
                    left_lines, right_lines,
                    fromfile=f"{left_date}/{left_file}",
                    tofile=f"{right_date}/{right_file}",
                    lineterm="",
                ))

                if diff:
                    left_pane = []
                    right_pane = []
                    for line in diff:
                        if line.startswith("---") or line.startswith("+++"):
                            continue
                        if line.startswith("@@"):
                            continue
                        if line.startswith("-"):
                            left_pane.append(f'<div class="diff-line diff-remove">{_esc(line[1:])}</div>')
                        elif line.startswith("+"):
                            right_pane.append(f'<div class="diff-line diff-add">{_esc(line[1:])}</div>')
                        else:
                            text = _esc(line[1:]) if line.startswith(" ") else _esc(line)
                            left_pane.append(f'<div class="diff-line diff-context">{text}</div>')
                            right_pane.append(f'<div class="diff-line diff-context">{text}</div>')

                    diff_html = (
                        f'<div class="compare-pane"><h3>{left_date} - {left_file}</h3>'
                        f'{"".join(left_pane)}</div>'
                        f'<div class="compare-pane"><h3>{right_date} - {right_file}</h3>'
                        f'{"".join(right_pane)}</div>'
                    )
                else:
                    diff_html = '<div class="empty-state"><p>Reports are identical</p></div>'
            except FileNotFoundError:
                diff_html = '<div class="empty-state"><p>Could not load one or both reports</p></div>'

        return html(
            templates.render_compare(
                dates, task_types,
                current_task=current_task,
                left_date=left_date, left_file=left_file,
                right_date=right_date, right_file=right_file,
                diff_html=diff_html,
                left_dates=left_dates, left_files=left_files,
                right_dates=right_dates, right_files=right_files,
                date_counts=counts,
            )
        )

    # --- Bookmarks ---

    @app.route("/bookmarks")
    async def bookmarks_page(request: Request):
        reader = _reader(request)
        bm_store = _bookmark_store(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)

        bookmarks = bm_store.list_bookmarks()
        bookmark_dicts = []
        for b in bookmarks:
            # Check if report still exists
            meta = reader.get_report_meta(b.date, b.filename)
            if meta:
                bookmark_dicts.append(_meta_to_dict(meta))

        return html(
            templates.render_bookmarks(dates, bookmark_dicts, date_counts=counts)
        )

    @app.route("/api/bookmarks", methods=["POST"])
    async def api_add_bookmark(request: Request):
        bm_store = _bookmark_store(request)
        try:
            data = request.json or {}
            date = data.get("date", "")
            filename = data.get("filename", "")
            if not date or not filename:
                return json_resp({"error": "date and filename required"}, status=400)
            bm = bm_store.add_bookmark(date, filename)
            return json_resp({"status": "ok", "bookmark": {
                "date": bm.date, "filename": bm.filename, "added_at": bm.added_at
            }})
        except Exception as e:
            return json_resp({"error": str(e)}, status=500)

    @app.route("/api/bookmarks", methods=["DELETE"])
    async def api_remove_bookmark(request: Request):
        bm_store = _bookmark_store(request)
        try:
            data = request.json or {}
            date = data.get("date", "")
            filename = data.get("filename", "")
            if not date or not filename:
                return json_resp({"error": "date and filename required"}, status=400)
            removed = bm_store.remove_bookmark(date, filename)
            return json_resp({"status": "ok" if removed else "not_found"})
        except Exception as e:
            return json_resp({"error": str(e)}, status=500)

    # --- Existing JSON API routes ---

    @app.route("/api/dates")
    async def api_dates(request: Request):
        reader = _reader(request)
        return json_resp({"dates": reader.list_dates()})

    @app.route("/api/reports/<date:str>")
    async def api_reports(request: Request, date: str):
        reader = _reader(request)
        task_type = request.args.get("task_type", "")
        reports = reader.list_reports(date, task_type=task_type or None)
        return json_resp(
            {"date": date, "reports": [_meta_to_dict(r) for r in reports]}
        )

    @app.route("/api/task-types")
    async def api_task_types(request: Request):
        reader = _reader(request)
        return json_resp({"task_types": reader.list_task_types()})

    # --- Semantic search (RAG) ---

    @app.route("/ask")
    async def ask_page(request: Request):
        reader = _reader(request)
        rag = _rag_service(request)
        dates = reader.list_dates()
        counts = _date_counts(reader, dates)
        query = request.args.get("q", "")
        results = []
        error = ""
        if query and rag and rag.available:
            try:
                results = await rag.search(query)
            except Exception as e:
                logger.error("RAG search failed: %s", e)
                error = str(e)
        elif query and (not rag or not rag.available):
            error = rag.init_error if rag else "RAG service not initialized"
        return html(
            templates.render_ask(
                dates,
                query=query,
                results=results,
                error=error,
                rag_available=rag.available if rag else False,
                rag_status=rag.get_status() if rag else {},
                date_counts=counts,
            )
        )

    @app.route("/api/ask", methods=["POST"])
    async def api_ask(request: Request):
        rag = _rag_service(request)
        if not rag or not rag.available:
            return json_resp({"error": "RAG service not available"}, status=503)
        try:
            data = request.json or {}
            query = data.get("query", "").strip()
            if not query:
                return json_resp({"error": "query required"}, status=400)
            results = await rag.search(query)
            status = rag.get_status()
            return json_resp({
                "results": [
                    {
                        "date": r.date,
                        "filename": r.filename,
                        "task_name": r.task_name,
                        "display_time": r.display_time,
                        "relevance": r.relevance,
                        "reasoning": r.reasoning,
                        "sections": r.sections,
                    }
                    for r in results
                ],
                "usage": status.get("usage", {}),
            })
        except Exception as e:
            return json_resp({"error": str(e)}, status=500)

    @app.route("/api/reindex", methods=["POST"])
    async def api_reindex(request: Request):
        rag = _rag_service(request)
        if not rag or not rag.available:
            return json_resp({"error": "RAG service not available"}, status=503)
        count = rag.build_index()
        return json_resp({"status": "ok", "indexed": count})

    @app.route("/api/generate-descriptions", methods=["POST"])
    async def api_generate_descriptions(request: Request):
        rag = _rag_service(request)
        if not rag or not rag.available:
            return json_resp({"error": "RAG service not available"}, status=503)
        try:
            count = await rag.generate_descriptions()
            return json_resp({"status": "ok", "generated": count})
        except Exception as e:
            return json_resp({"error": str(e)}, status=500)

    @app.route("/api/rag/status")
    async def api_rag_status(request: Request):
        rag = _rag_service(request)
        if not rag:
            return json_resp({"available": False})
        return json_resp(rag.get_status())


def _esc(text: str) -> str:
    """HTML-escape text for safe rendering"""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
