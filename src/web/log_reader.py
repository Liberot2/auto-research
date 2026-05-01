"""Log reader - execution log file discovery and parsing"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_FILENAME_RE = re.compile(r"^(.+?)_(\d{6})\.txt$")


@dataclass
class LogEntry:
    """Parsed structured log entry"""

    date: str  # "2026-04-17"
    task_name: str  # "morning_papers"
    time_str: str  # "221003"
    filename: str  # "morning_papers_221003.txt"
    path: Path  # absolute path
    skill: str = ""
    timestamp: str = ""
    success: bool = False
    cost: str | None = None
    duration: str | None = None
    turns: int | None = None
    prompt: str = ""
    result: str = ""

    @property
    def display_time(self) -> str:
        """Format HHMMSS as HH:MM:SS"""
        return f"{self.time_str[:2]}:{self.time_str[2:4]}:{self.time_str[4:6]}"


class LogReader:
    """Read and parse execution log files from the logs directory"""

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir

    def list_dates(self) -> list[str]:
        """Scan log_dir for YYYY-MM-DD subdirectories, sorted descending"""
        if not self.log_dir.is_dir():
            return []
        dates: list[str] = []
        for p in self.log_dir.iterdir():
            if p.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", p.name):
                dates.append(p.name)
        dates.sort(reverse=True)
        return dates

    def list_logs(
        self, date: str, task_name: str | None = None
    ) -> list[LogEntry]:
        """List log files for a date, optionally filtered by task name"""
        date_dir = self.log_dir / date
        if not date_dir.is_dir():
            return []
        entries: list[LogEntry] = []
        for p in sorted(date_dir.iterdir(), reverse=True):
            if not p.is_file():
                continue
            m = _FILENAME_RE.match(p.name)
            if not m:
                continue
            tname, time_str = m.group(1), m.group(2)
            if task_name and tname != task_name:
                continue
            entries.append(
                LogEntry(
                    date=date,
                    task_name=tname,
                    time_str=time_str,
                    filename=p.name,
                    path=p,
                )
            )
        return entries

    def read_log(self, date: str, filename: str) -> str:
        """Read raw log file content"""
        path = self.log_dir / date / filename
        if not path.is_file():
            raise FileNotFoundError(f"Log not found: {path}")
        return path.read_text(encoding="utf-8")

    def parse_log(self, date: str, filename: str) -> LogEntry | None:
        """Parse structured log file into LogEntry"""
        try:
            content = self.read_log(date, filename)
        except FileNotFoundError:
            return None

        m = _FILENAME_RE.match(filename)
        if not m:
            return None

        entry = LogEntry(
            date=date,
            task_name=m.group(1),
            time_str=m.group(2),
            filename=filename,
            path=self.log_dir / date / filename,
        )

        lines = content.split("\n")

        # Parse header key-value pairs
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("--- "):
                break
            if line.startswith("Task:"):
                entry.skill = lines[i][len("Task:"):].strip() if i < len(lines) else ""
                # skill field in log is same as task_name; actual skill name is on Skill: line
            elif line.startswith("Skill:"):
                entry.skill = line[len("Skill:"):].strip()
            elif line.startswith("Time:"):
                entry.timestamp = line[len("Time:"):].strip()
            elif line.startswith("Success:"):
                entry.success = line[len("Success:"):].strip().lower() == "true"
            elif line.startswith("Cost:"):
                entry.cost = line[len("Cost:"):].strip()
            elif line.startswith("Duration:"):
                raw = line[len("Duration:"):].strip()
                try:
                    ms = int(raw.replace("ms", ""))
                    entry.duration = f"{ms / 1000:.1f}s"
                except ValueError:
                    entry.duration = raw
            elif line.startswith("Turns:"):
                try:
                    entry.turns = int(line[len("Turns:"):].strip())
                except ValueError:
                    pass
            i += 1

        # Extract Prompt section
        prompt_start = _find_section(lines, "--- Prompt ---")
        result_start = _find_section(lines, "--- Result ---")
        error_start = _find_section(lines, "--- Error ---")

        if prompt_start >= 0:
            end = result_start if result_start >= 0 else error_start if error_start >= 0 else len(lines)
            entry.prompt = "\n".join(lines[prompt_start + 1:end]).strip()

        if result_start >= 0:
            entry.result = "\n".join(lines[result_start + 1:]).strip()
        elif error_start >= 0:
            entry.result = "\n".join(lines[error_start + 1:]).strip()

        return entry

    def get_latest_for_task(self, task_name: str) -> LogEntry | None:
        """Find the most recent log entry for a task across all dates"""
        for date in self.list_dates():
            logs = self.list_logs(date, task_name=task_name)
            if logs:
                entry = logs[0]  # sorted descending, first is latest
                parsed = self.parse_log(date, entry.filename)
                if parsed:
                    return parsed
        return None

    def get_history_for_task(self, task_name: str) -> list[LogEntry]:
        """Return all log entries for a task, sorted newest first"""
        results: list[LogEntry] = []
        for date in self.list_dates():
            for meta in self.list_logs(date, task_name=task_name):
                parsed = self.parse_log(date, meta.filename)
                if parsed:
                    results.append(parsed)
        return results

    def get_log_meta(self, date: str, filename: str) -> LogEntry | None:
        """Get basic metadata for a log file without full parsing"""
        m = _FILENAME_RE.match(filename)
        if not m:
            return None
        path = self.log_dir / date / filename
        if not path.is_file():
            return None
        return LogEntry(
            date=date,
            task_name=m.group(1),
            time_str=m.group(2),
            filename=filename,
            path=path,
        )


def _find_section(lines: list[str], marker: str) -> int:
    """Find the index of a section marker like --- Prompt ---"""
    for i, line in enumerate(lines):
        if line.strip() == marker:
            return i
    return -1
