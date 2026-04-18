"""HTTP request handlers for the report viewer web service"""

import logging

import mistune
from sanic import Sanic
from sanic.request import Request
from sanic.response import html, json as json_resp

from src.web.report_reader import ReportReader
from src.web import templates

logger = logging.getLogger(__name__)

_md = mistune.create_markdown(plugins=["table", "strikethrough", "task_lists"])


def _reader(request: Request) -> ReportReader:
    return request.app.ctx.reader


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
        return html(
            templates.render_report(
                dates, date, filename, title, html_content, date_counts=counts
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
