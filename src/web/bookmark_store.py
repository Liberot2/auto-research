"""Bookmark store - JSON-based report bookmark persistence"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Bookmark:
    """A bookmarked report"""

    date: str  # "2026-04-17"
    filename: str  # "morning_papers_221002_report.md"
    task_name: str  # derived from filename
    added_at: str  # ISO timestamp when bookmarked


class BookmarkStore:
    """Simple JSON file-based bookmark storage"""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._path = data_dir / "bookmarks.json"

    def _load(self) -> list[dict]:
        """Load bookmarks from JSON file"""
        if not self._path.is_file():
            return []
        try:
            text = self._path.read_text(encoding="utf-8")
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            logger.warning("Failed to load bookmarks from %s", self._path)
            return []

    def _save(self, bookmarks: list[dict]) -> None:
        """Save bookmarks to JSON file"""
        self._path.write_text(
            json.dumps(bookmarks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_bookmarks(self) -> list[Bookmark]:
        """List all bookmarks, sorted by added_at descending"""
        raw = self._load()
        bookmarks = []
        for item in raw:
            bookmarks.append(
                Bookmark(
                    date=item.get("date", ""),
                    filename=item.get("filename", ""),
                    task_name=_extract_task_name(item.get("filename", "")),
                    added_at=item.get("added_at", ""),
                )
            )
        bookmarks.sort(key=lambda b: b.added_at, reverse=True)
        return bookmarks

    def add_bookmark(self, date: str, filename: str) -> Bookmark:
        """Add a bookmark, no-op if already exists"""
        bookmarks = self._load()
        # Check for duplicate
        for item in bookmarks:
            if item.get("date") == date and item.get("filename") == filename:
                return Bookmark(
                    date=date,
                    filename=filename,
                    task_name=_extract_task_name(filename),
                    added_at=item.get("added_at", ""),
                )
        now = datetime.now().isoformat()
        new_item = {"date": date, "filename": filename, "added_at": now}
        bookmarks.append(new_item)
        self._save(bookmarks)
        return Bookmark(
            date=date,
            filename=filename,
            task_name=_extract_task_name(filename),
            added_at=now,
        )

    def remove_bookmark(self, date: str, filename: str) -> bool:
        """Remove a bookmark by date + filename"""
        bookmarks = self._load()
        original_len = len(bookmarks)
        bookmarks = [
            b for b in bookmarks
            if not (b.get("date") == date and b.get("filename") == filename)
        ]
        if len(bookmarks) < original_len:
            self._save(bookmarks)
            return True
        return False

    def is_bookmarked(self, date: str, filename: str) -> bool:
        """Check if a report is bookmarked"""
        bookmarks = self._load()
        return any(
            b.get("date") == date and b.get("filename") == filename
            for b in bookmarks
        )


def _extract_task_name(filename: str) -> str:
    """Extract task name from report filename like 'morning_papers_221002_report.md'"""
    import re

    m = re.match(r"^(.+?)_\d{6}_report\.md$", filename)
    return m.group(1) if m else filename
