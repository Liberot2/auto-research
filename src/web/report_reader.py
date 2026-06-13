"""Report reader - report file discovery and content loading"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_FILENAME_RE = re.compile(r"^(.+?)_(\d{6})_report\.md$")


@dataclass
class ReportMeta:
    """Metadata for a single report file"""

    date: str  # "2026-04-17"
    task_name: str  # "morning_papers"
    time_str: str  # "221002"
    filename: str  # full filename
    path: Path  # absolute path

    @property
    def display_time(self) -> str:
        """Format HHMMSS as HH:MM:SS"""
        return f"{self.time_str[:2]}:{self.time_str[2:4]}:{self.time_str[4:6]}"


@dataclass
class DaySummary:
    """Summary of reports for one date"""

    date: str
    reports: list[ReportMeta] = field(default_factory=list)


class ReportReader:
    """Read and search report files from the reports directory"""

    def __init__(self, report_dir: Path, research_dir: Path | None = None) -> None:
        self.report_dir = report_dir
        self.research_dir = research_dir

    def list_dates(self) -> list[str]:
        """Scan report_dir for YYYY-MM-DD subdirectories, sorted descending"""
        dates: set[str] = set()
        if self.report_dir.is_dir():
            for p in self.report_dir.iterdir():
                if p.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", p.name):
                    dates.add(p.name)
        # Include dates from research projects
        if self.research_dir and self.research_dir.is_dir():
            for p in self.research_dir.iterdir():
                state = p / "state.md"
                if p.is_dir() and state.is_file():
                    d = self._parse_research_date(state)
                    if d:
                        dates.add(d)
        result = sorted(dates, reverse=True)
        return result

    def _parse_research_date(self, state_path: Path) -> str | None:
        """Extract last_updated date from research state.md"""
        try:
            content = state_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("- last_updated:"):
                    val = line.split(":", 1)[1].strip().strip('"')
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", val):
                        return val
        except OSError:
            pass
        return None

    def _list_research_as_reports(self, date: str) -> list[ReportMeta]:
        """Scan research projects updated on given date, return as virtual report entries"""
        if not self.research_dir or not self.research_dir.is_dir():
            return []
        reports: list[ReportMeta] = []
        for p in sorted(self.research_dir.iterdir()):
            if not p.is_dir():
                continue
            state = p / "state.md"
            if not state.is_file():
                continue
            d = self._parse_research_date(state)
            if d != date:
                continue
            solution = p / "solution.md"
            if not solution.is_file():
                continue
            # Virtual filename: research_{slug}_{HHMMSS}_report.md
            reports.append(
                ReportMeta(
                    date=date,
                    task_name=f"research/{p.name}",
                    time_str="000000",
                    filename=f"research_{p.name}_000000_report.md",
                    path=solution,
                )
            )
        return reports

    def list_reports(
        self, date: str, task_type: str | None = None
    ) -> list[ReportMeta]:
        """List reports for a date, optionally filtered by task type"""
        reports: list[ReportMeta] = []
        date_dir = self.report_dir / date
        if date_dir.is_dir():
            for p in sorted(date_dir.iterdir()):
                if not p.is_file():
                    continue
                m = _FILENAME_RE.match(p.name)
                if not m:
                    continue
                task_name, time_str = m.group(1), m.group(2)
                if task_type and task_name != task_type:
                    continue
                reports.append(
                    ReportMeta(
                    date=date,
                    task_name=task_name,
                    time_str=time_str,
                    filename=p.name,
                    path=p,
                )
            )
        # Append research solutions for this date
        if not task_type or task_type.startswith("research"):
            reports.extend(self._list_research_as_reports(date))
        return reports

    def read_report(self, date: str, filename: str) -> str:
        """Read a single report file content"""
        # Check if it's a research solution file
        if filename.startswith("research_") and filename.endswith("_000000_report.md"):
            slug = filename[len("research_"):-len("_000000_report.md")]
            if self.research_dir:
                path = self.research_dir / slug / "solution.md"
                if path.is_file():
                    return path.read_text(encoding="utf-8")
        path = self.report_dir / date / filename
        if not path.is_file():
            raise FileNotFoundError(f"Report not found: {path}")
        return path.read_text(encoding="utf-8")

    def search_reports(
        self,
        query: str,
        task_type: str | None = None,
        date: str | None = None,
    ) -> list[ReportMeta]:
        """Full-text search across report files (case-insensitive)"""
        query_lower = query.lower()
        results: list[ReportMeta] = []
        dates = [date] if date else self.list_dates()
        for d in dates:
            for meta in self.list_reports(d, task_type=task_type):
                try:
                    content = meta.path.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        results.append(meta)
                except OSError:
                    logger.warning("Failed to read report: %s", meta.path)
        return results

    def list_task_types(self) -> list[str]:
        """Extract unique task names from all report filenames"""
        types: set[str] = set()
        for d in self.list_dates():
            for meta in self.list_reports(d):
                types.add(meta.task_name)
        return sorted(types)

    def get_report_meta(self, date: str, filename: str) -> ReportMeta | None:
        """Get metadata for a specific report file"""
        # Check if it's a research solution file
        if filename.startswith("research_") and filename.endswith("_000000_report.md"):
            slug = filename[len("research_"):-len("_000000_report.md")]
            if self.research_dir:
                path = self.research_dir / slug / "solution.md"
                if path.is_file():
                    return ReportMeta(
                        date=date,
                        task_name=f"research/{slug}",
                        time_str="000000",
                        filename=filename,
                        path=path,
                    )
            return None
        m = _FILENAME_RE.match(filename)
        if not m:
            return None
        path = self.report_dir / date / filename
        if not path.is_file():
            return None
        return ReportMeta(
            date=date,
            task_name=m.group(1),
            time_str=m.group(2),
            filename=filename,
            path=path,
        )
