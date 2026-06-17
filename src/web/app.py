"""Sanic web application factory for report viewer"""

import asyncio
import logging
import sys
from pathlib import Path

from sanic import Sanic

# Windows ProactorEventLoop supports subprocess creation (needed by claude_agent_sdk)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # Sanic's startup.setup_loop() would override our Proactor policy with
    # WindowsSelectorEventLoopPolicy, but SelectorEventLoop cannot spawn
    # subprocesses — required when /api/research/<slug>/advance runs the
    # deep_research skill via claude_agent_sdk (anyio.open_process fails with
    # NotImplementedError). Disable the override on both import sites.
    import sanic.mixins.startup as _sanic_startup
    import sanic.server.loop as _sanic_loop

    _sanic_startup.try_windows_loop = lambda: None
    _sanic_loop.try_windows_loop = lambda: None

from src.web.handlers import register_routes
from src.web.report_reader import ReportReader

logger = logging.getLogger(__name__)


def create_app(
    report_dir: Path,
    config_path: Path | None = None,
) -> Sanic:
    """Create and configure the Sanic application"""
    app = Sanic("ReportViewer")
    research_dir = report_dir.parent / "data" / "research"
    app.ctx.reader = ReportReader(report_dir, research_dir=research_dir)

    # Log reader
    from src.web.log_reader import LogReader

    log_dir = report_dir.parent / "logs"
    if config_path and config_path.exists():
        import yaml

        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        ld = cfg.get("log_dir", "logs")
        log_dir = Path(ld)
        if not log_dir.is_absolute():
            log_dir = config_path.parent.parent / ld
    app.ctx.log_reader = LogReader(log_dir)

    # Bookmark store
    from src.web.bookmark_store import BookmarkStore

    data_dir = report_dir.parent / "data"
    app.ctx.bookmark_store = BookmarkStore(data_dir)

    # Task runner (optional)
    app.ctx.task_runner = None
    app.ctx.config_path = None
    if config_path and config_path.exists():
        from src.core.runner import TaskRunner

        runner = TaskRunner(config_path=config_path)
        runner.load_config()
        app.ctx.task_runner = runner
        app.ctx.config_path = config_path

    # Load workspace .env for LLM API keys (before PageIndex import)
    pageindex_path = report_dir.parent / ".." / "PageIndex"
    workspace_env = report_dir.resolve().parent.parent / ".env"
    if workspace_env.exists():
        from dotenv import load_dotenv
        load_dotenv(workspace_env, override=True)
        logger.info("Loaded workspace .env from %s", workspace_env)

    # RAG service (optional, requires PageIndex)
    from src.web.rag_service import RagService

    data_dir = report_dir.parent / "data"

    rag = RagService(report_dir, data_dir / "rag_index", str(pageindex_path))
    if rag.available:
        rag.build_index()
    app.ctx.rag_service = rag

    register_routes(app)

    # Research project routes (optional)
    try:
        from src.web.research_handlers import register_research_routes
        register_research_routes(app)
    except ImportError:
        logger.debug("Research module not available")

    return app


def run_server(
    report_dir: Path,
    config_path: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Start the report viewer web server"""
    app = create_app(report_dir, config_path=config_path)
    logger.info("Starting report viewer at http://%s:%d", host, port)
    app.run(host=host, port=port, single_process=True, motd=False)
