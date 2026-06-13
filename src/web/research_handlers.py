"""Research project web routes"""

import logging
import re
from pathlib import Path

import mistune
from sanic import Sanic, response

from src.web.research_reader import ResearchReader
from src.web import templates as tpl

logger = logging.getLogger(__name__)

_md = mistune.create_markdown()


def _get_reader(app: Sanic) -> ResearchReader:
    """Get or create the ResearchReader from app context"""
    if not hasattr(app.ctx, "research_reader") or app.ctx.research_reader is None:
        research_dir = (
            app.ctx.config_path.parent.parent / "data" / "research"
            if app.ctx.config_path
            else Path("data/research")
        )
        app.ctx.research_reader = ResearchReader(research_dir)
    return app.ctx.research_reader


def _date_counts(reader, dates: list[str]) -> dict[str, int]:
    """Build date -> report count mapping"""
    return {d: len(reader.list_reports(d)) for d in dates}


# ── Page Handlers ──────────────────────────────────────────────────────


async def research_list(request):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    projects = _get_reader(app).list_projects()
    html = tpl.render_research_list(dates, projects, date_counts)
    return response.html(html)


async def research_detail(request, slug):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.html(tpl.render_error(dates, f"Project '{slug}' not found", date_counts))
    state_content = reader.read_state(slug)
    sessions = reader.list_sessions(slug)
    html = tpl.render_research_detail(dates, project, state_content, sessions, date_counts)
    return response.html(html)


async def research_solution(request, slug):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.html(tpl.render_error(dates, f"Project '{slug}' not found", date_counts))
    content = reader.read_solution(slug)
    html_content = _md(content) if content else "<p>Solution document not yet created.</p>"
    html = tpl.render_research_solution(dates, slug, project.topic, html_content, date_counts)
    return response.html(html)


async def research_checklist(request, slug):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.html(tpl.render_error(dates, f"Project '{slug}' not found", date_counts))
    content = reader.read_checklist(slug)
    html_content = _md(content) if content else "<p>Checklist not yet created.</p>"
    html = tpl.render_research_checklist(dates, slug, project.topic, html_content, date_counts)
    return response.html(html)


async def research_todo(request, slug):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.html(tpl.render_error(dates, f"Project '{slug}' not found", date_counts))
    content = reader.read_todo(slug)
    html_content = _md(content) if content else "<p>Research TODO not yet created.</p>"
    html = tpl.render_research_todo(dates, slug, project.topic, html_content, date_counts)
    return response.html(html)
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.html(tpl.render_error(dates, f"Project '{slug}' not found", date_counts))
    content = reader.read_todo(slug)
    html_content = _md(content) if content else "<p>Research TODO not yet created.</p>"
    html = tpl.render_research_todo(dates, slug, project.topic, html_content, date_counts)
    return response.html(html)


async def research_sessions(request, slug):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.html(tpl.render_error(dates, f"Project '{slug}' not found", date_counts))
    sessions = reader.list_sessions(slug)
    html = tpl.render_research_sessions(dates, slug, project.topic, sessions, date_counts)
    return response.html(html)


async def research_session_detail(request, slug, filename):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    reader = _get_reader(app)
    content = reader.read_session(slug, filename)
    if not content:
        return response.html(tpl.render_error(dates, f"Session '{filename}' not found", date_counts))
    html_content = _md(content)
    body = f"""
<div class="layout">
{tpl._sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Session: {filename}</h1></div>
    <div class="action-bar">
        <a href="/research/{slug}/sessions" class="back-link">&larr; Sessions</a>
    </div>
    <div class="report-content">{html_content}</div>
</div>
</div>"""
    return response.html(tpl._page(f"Session - {filename}", body))


async def research_new(request):
    app = request.app
    dates = app.ctx.reader.list_dates()
    date_counts = _date_counts(app.ctx.reader, dates)
    html = tpl.render_research_new(dates, date_counts)
    return response.html(html)


# ── API Handlers ───────────────────────────────────────────────────────


async def api_research_list(request):
    projects = _get_reader(request.app).list_projects()
    return response.json([
        {
            "slug": p.slug,
            "topic": p.topic,
            "phase": p.phase,
            "status": p.status,
            "confidence": p.confidence,
            "total_sessions": p.total_sessions,
            "last_updated": p.last_updated,
        }
        for p in projects
    ])


async def api_research_detail(request, slug):
    project = _get_reader(request.app).get_project(slug)
    if not project:
        return response.json({"error": f"Project '{slug}' not found"}, status=404)
    return response.json({
        "slug": project.slug,
        "topic": project.topic,
        "phase": project.phase,
        "status": project.status,
        "confidence": project.confidence,
        "total_sessions": project.total_sessions,
        "last_updated": project.last_updated,
        "source_count": project.source_count,
        "session_count": project.session_count,
    })


async def api_research_create(request):
    data = request.json or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return response.json({"error": "topic is required"}, status=400)

    # Generate slug from topic
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", topic.lower())[:60].strip("-")
    if not slug:
        reader = _get_reader(request.app)
        slug = f"project-{len(reader.list_projects()) + 1}"

    reader = _get_reader(request.app)
    existing = reader.get_project(slug)
    if existing:
        return response.json({"error": f"Project '{slug}' already exists", "slug": slug}, status=409)

    try:
        project = reader.create_project(slug, topic)
        return response.json({
            "slug": project.slug,
            "topic": project.topic,
            "phase": project.phase,
        }, status=201)
    except Exception as e:
        logger.error("Failed to create project: %s", e, exc_info=True)
        return response.json({"error": str(e)}, status=500)


async def api_research_advance(request, slug):
    """Trigger a research run for a project via the task runner"""
    app = request.app
    runner = app.ctx.task_runner
    if not runner:
        return response.json({"error": "Task runner not configured"}, status=503)

    reader = _get_reader(app)
    project = reader.get_project(slug)
    if not project:
        return response.json({"error": f"Project '{slug}' not found"}, status=404)

    if project.phase == "complete":
        return response.json({"error": "Research already completed"}, status=400)

    # Build a temporary task config and run it
    task_name = f"research_{slug}"
    task_config = {
        "skill": "deep_research",
        "type": "research",
        "description": project.topic,
        "enabled": True,
        "max_turns": 200,
        "parameters": {
            "project": slug,
            "topic": project.topic,
            "max_depth": 3,
        },
    }

    # Add the temporary task to runner config
    runner.tasks_config[task_name] = task_config

    try:
        result = await runner.run_task(task_name)
        return response.json({
            "success": result.success,
            "error": result.error,
            "slug": slug,
        })
    except Exception as e:
        return response.json({"error": str(e)}, status=500)
    finally:
        runner.tasks_config.pop(task_name, None)


# ── Registration ───────────────────────────────────────────────────────


def register_research_routes(app: Sanic) -> None:
    """Register research project routes with the Sanic app"""
    # Initialize reader lazily via _get_reader()
    app.ctx.research_reader = None

    app.add_route(research_list, "/research")
    app.add_route(research_detail, "/research/<slug>")
    app.add_route(research_solution, "/research/<slug>/solution")
    app.add_route(research_checklist, "/research/<slug>/checklist")
    app.add_route(research_todo, "/research/<slug>/todo")
    app.add_route(research_sessions, "/research/<slug>/sessions")
    app.add_route(research_session_detail, "/research/<slug>/sessions/<filename>")
    app.add_route(research_new, "/research/new")
    app.add_route(api_research_list, "/api/research", methods=["GET"])
    app.add_route(api_research_detail, "/api/research/<slug>", methods=["GET"])
    app.add_route(api_research_create, "/api/research/create", methods=["POST"])
    app.add_route(api_research_advance, "/api/research/<slug>/advance", methods=["POST"])
