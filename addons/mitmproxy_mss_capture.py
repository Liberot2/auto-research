"""mitmproxy addon for capturing MSS platform HTTP actions.

Records API requests/responses into structured JSON files for SOP generation.
Filters out static resources and non-MSS domain requests.

Usage: mitmproxy -s addons/mitmproxy_mss_capture.py --set mss_domain=example.com
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mitmproxy import http, ctx

logger = logging.getLogger(__name__)

# File extensions to skip (static resources)
STATIC_EXTENSIONS = frozenset({
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".svg", ".woff", ".woff2", ".ttf", ".eot", ".map",
    ".mp4", ".mp3", ".wav", ".avi", ".pdf",
})

# Headers to redact for security
SENSITIVE_HEADERS = frozenset({
    "authorization", "cookie", "set-cookie",
    "x-csrf-token", "x-xsrf-token",
})

# Max response body size to capture (10KB)
MAX_RESPONSE_BODY = 10 * 1024

# Session timeout: 30 minutes of inactivity triggers a flush
SESSION_TIMEOUT_SECONDS = 30 * 60


class MssCaptureAddon:
    """Captures MSS platform HTTP actions into JSON session files."""

    def __init__(self) -> None:
        self.mss_domain: str = ""
        self.output_dir: Path = Path("data/mss_captures")
        self.actions: list[dict[str, Any]] = []
        self.session_start: datetime | None = None
        self.last_request_time: float = 0
        self.sequence: int = 0
        self.request_timestamps: dict[str, float] = {}

    def load(self, loader: Any) -> None:
        """Load configuration from mitmproxy options."""
        loader.add_option(
            name="mss_domain",
            typespec=str,
            default="",
            help="MSS platform domain to capture (e.g., mss.example.com)",
        )
        loader.add_option(
            name="output_dir",
            typespec=str,
            default="data/mss_captures",
            help="Directory to save capture JSON files",
        )

    def configure(self, updated: set[str]) -> None:
        """Apply configuration changes."""
        if "mss_domain" in updated:
            self.mss_domain = getattr(ctx.options, "mss_domain", "")
        if "output_dir" in updated:
            self.output_dir = Path(getattr(ctx.options, "output_dir", "data/mss_captures"))
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def _should_capture(self, flow: http.HTTPFlow) -> bool:
        """Check if this request should be captured."""
        # Must target MSS domain
        if self.mss_domain and self.mss_domain not in flow.request.pretty_host:
            return False

        # Skip static resources by file extension
        path = flow.request.path.split("?")[0]
        ext = Path(path).suffix.lower()
        if ext in STATIC_EXTENSIONS:
            return False

        return True

    def _redact_headers(self, headers: http.Headers) -> dict[str, str]:
        """Copy headers, redacting sensitive ones."""
        result = {}
        for k, v in headers.items():
            if k.lower() in SENSITIVE_HEADERS:
                result[k] = "***REDACTED***"
            else:
                result[k] = v
        return result

    def _safe_body(self, body: bytes, max_size: int = MAX_RESPONSE_BODY) -> Any:
        """Parse body as JSON, fallback to string, truncated."""
        if not body:
            return None
        try:
            text = body[:max_size].decode("utf-8", errors="replace")
            return json.loads(text)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return body[:max_size].decode("utf-8", errors="replace")

    def request(self, flow: http.HTTPFlow) -> None:
        """Record request details."""
        if not self._should_capture(flow):
            return

        now = time.time()

        # Flush session if timeout exceeded
        if self.last_request_time and (now - self.last_request_time) > SESSION_TIMEOUT_SECONDS:
            self._flush_session()

        if self.session_start is None:
            self.session_start = datetime.now(timezone.utc)

        self.sequence += 1
        self.last_request_time = now

        # Store request timestamp for duration calculation
        self.request_timestamps[flow.id] = now

        # Parse query params
        query_params: dict[str, str] = {}
        if flow.request.query:
            query_params = dict(flow.request.query.items())

        # Parse request body
        request_body = self._safe_body(flow.request.content) if flow.request.content else None

        action = {
            "sequence": self.sequence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "path": flow.request.path,
            "query_params": query_params or None,
            "request_headers": self._redact_headers(flow.request.headers),
            "request_body": request_body,
            "response_status": None,
            "response_body": None,
            "duration_ms": None,
        }

        # Store action temporarily; response hook will complete it
        flow.metadata["mss_capture_index"] = len(self.actions)
        self.actions.append(action)

    def response(self, flow: http.HTTPFlow) -> None:
        """Record response details and complete the action."""
        if "mss_capture_index" not in flow.metadata:
            return

        idx = flow.metadata["mss_capture_index"]
        if idx >= len(self.actions):
            return

        action = self.actions[idx]
        action["response_status"] = flow.response.status_code

        # Parse response body (truncated)
        if flow.response.content:
            action["response_body"] = self._safe_body(flow.response.content)

        # Calculate duration
        req_time = self.request_timestamps.pop(flow.id, None)
        if req_time:
            action["duration_ms"] = int((time.time() - req_time) * 1000)

    def _flush_session(self) -> None:
        """Write current session to JSON file and reset state."""
        if not self.actions:
            return

        if self.session_start is None:
            return

        session_id = f"session_{self.session_start.strftime('%Y%m%d_%H%M%S')}"
        session = {
            "session_id": session_id,
            "start_time": self.session_start.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "source": "mitmproxy",
            "mss_base_url": f"https://{self.mss_domain}" if self.mss_domain else "",
            "action_count": len(self.actions),
            "actions": self.actions,
        }

        output_path = self.output_dir / f"{session_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)

        logger.info("Flushed capture session: %s (%d actions)", session_id, len(self.actions))

        # Reset state
        self.actions = []
        self.sequence = 0
        self.session_start = None
        self.request_timestamps.clear()

    def done(self) -> None:
        """Flush remaining actions on shutdown."""
        self._flush_session()


addons = [MssCaptureAddon()]
