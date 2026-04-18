"""Sanic web application factory for report viewer"""

import logging
from pathlib import Path

from sanic import Sanic

from src.web.handlers import register_routes
from src.web.report_reader import ReportReader

logger = logging.getLogger(__name__)


def create_app(report_dir: Path) -> Sanic:
    """Create and configure the Sanic application"""
    app = Sanic("ReportViewer")
    app.ctx.reader = ReportReader(report_dir)
    register_routes(app)
    return app


def run_server(
    report_dir: Path, host: str = "127.0.0.1", port: int = 8000
) -> None:
    """Start the report viewer web server"""
    app = create_app(report_dir)
    logger.info("Starting report viewer at http://%s:%d", host, port)
    app.run(host=host, port=port, single_process=True, motd=False)
