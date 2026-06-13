"""Research project reader - scans data/research/ directory for project state"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_PHASES = ["discovery", "analysis", "solution_draft", "validation", "finalization", "complete"]


@dataclass
class SourceFile:
    """Research source file metadata"""

    filename: str
    path: Path


@dataclass
class SessionMeta:
    """Research session metadata"""

    filename: str
    path: Path
    timestamp: str = ""


@dataclass
class ResearchProject:
    """Research project state"""

    slug: str
    path: Path
    topic: str = ""
    phase: str = "discovery"
    status: str = "in_progress"
    confidence: int = 0
    total_sessions: int = 0
    created: str = ""
    last_updated: str = ""
    next_action: str = ""
    has_solution: bool = False
    has_checklist: bool = False
    has_todo: bool = False
    source_count: int = 0
    session_count: int = 0
    todo_completed: int = 0
    todo_pending: int = 0


class ResearchReader:
    """Read research project data from data/research/ directory"""

    def __init__(self, research_dir: Path) -> None:
        self.research_dir = research_dir

    def list_projects(self) -> list[ResearchProject]:
        """List all research projects"""
        if not self.research_dir.exists():
            return []

        projects = []
        for d in sorted(self.research_dir.iterdir()):
            if d.is_dir() and (d / "state.md").exists():
                project = self._parse_project(d)
                if project:
                    projects.append(project)
        return projects

    def get_project(self, slug: str) -> ResearchProject | None:
        """Get a specific research project by slug"""
        project_dir = self.research_dir / slug
        if not project_dir.exists() or not (project_dir / "state.md").exists():
            return None
        return self._parse_project(project_dir)

    def read_state(self, slug: str) -> str:
        """Read raw state.md content"""
        state_path = self.research_dir / slug / "state.md"
        if not state_path.exists():
            return ""
        return state_path.read_text(encoding="utf-8")

    def read_solution(self, slug: str) -> str:
        """Read raw solution.md content"""
        solution_path = self.research_dir / slug / "solution.md"
        if not solution_path.exists():
            return ""
        return solution_path.read_text(encoding="utf-8")

    def read_checklist(self, slug: str) -> str:
        """Read raw checklist.md content"""
        checklist_path = self.research_dir / slug / "checklist.md"
        if not checklist_path.exists():
            return ""
        return checklist_path.read_text(encoding="utf-8")

    def read_todo(self, slug: str) -> str:
        """Read raw research-todo.md content"""
        todo_path = self.research_dir / slug / "research-todo.md"
        if not todo_path.exists():
            return ""
        return todo_path.read_text(encoding="utf-8")

    def read_session(self, slug: str, filename: str) -> str:
        """Read a specific session log"""
        session_path = self.research_dir / slug / "sessions" / filename
        if not session_path.exists():
            return ""
        return session_path.read_text(encoding="utf-8")

    def list_sources(self, slug: str) -> list[SourceFile]:
        """List source files for a project"""
        sources_dir = self.research_dir / slug / "sources"
        if not sources_dir.exists():
            return []
        return [
            SourceFile(filename=f.name, path=f)
            for f in sorted(sources_dir.iterdir())
            if f.is_file() and f.suffix == ".md"
        ]

    def list_sessions(self, slug: str) -> list[SessionMeta]:
        """List session logs for a project"""
        sessions_dir = self.research_dir / slug / "sessions"
        if not sessions_dir.exists():
            return []
        sessions = []
        for f in sorted(sessions_dir.iterdir(), reverse=True):
            if f.is_file() and f.suffix == ".md":
                # Extract timestamp from filename: YYYY-MM-DD_HHMMSS.md
                ts_match = re.match(r"(\d{4}-\d{2}-\d{2}_\d{6})", f.stem)
                ts = ts_match.group(1) if ts_match else f.stem
                sessions.append(SessionMeta(filename=f.name, path=f, timestamp=ts))
        return sessions

    def create_project(self, slug: str, topic: str) -> ResearchProject:
        """Create a new research project with initial state files"""
        from datetime import datetime

        project_dir = self.research_dir / slug
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "sessions").mkdir(exist_ok=True)
        (project_dir / "sources").mkdir(exist_ok=True)
        (project_dir / "artifacts").mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Read templates from skill assets
        skill_dir = self.research_dir.parent.parent / ".claude" / "skills" / "deep-research" / "assets"

        # state.md
        state_content = self._fill_template(
            skill_dir / "state-template.md",
            {"project": slug, "topic": topic, "timestamp": ts},
        )
        (project_dir / "state.md").write_text(state_content, encoding="utf-8")

        # solution.md
        solution_content = self._fill_template(
            skill_dir / "solution-template.md",
            {"topic": topic},
        )
        (project_dir / "solution.md").write_text(solution_content, encoding="utf-8")

        # checklist.md
        checklist_content = self._fill_template(
            skill_dir / "checklist-template.md",
            {"topic": topic},
        )
        (project_dir / "checklist.md").write_text(checklist_content, encoding="utf-8")

        logger.info("Created research project: %s", slug)
        return self._parse_project(project_dir)

    def _parse_project(self, project_dir: Path) -> ResearchProject | None:
        """Parse project state from state.md"""
        state_path = project_dir / "state.md"
        if not state_path.exists():
            return None

        try:
            content = state_path.read_text(encoding="utf-8")
            slug = project_dir.name

            # Parse key fields from state.md
            topic = self._extract_field(content, "topic") or slug
            phase = self._extract_field(content, "Current Phase") or "discovery"
            status = self._extract_field(content, "Status") or "in_progress"
            confidence_str = self._extract_field(content, "Confidence") or "0%"
            confidence = int(re.sub(r"[^\d]", "", confidence_str) or "0")
            sessions_str = self._extract_field(content, "total_sessions") or "0"
            total_sessions = int(re.sub(r"[^\d]", "", sessions_str) or "0")
            created = self._extract_field(content, "created") or ""
            last_updated = self._extract_field(content, "last_updated") or ""
            next_action = self._extract_field(content, "Next Action") or ""

            # Count files
            sources_dir = project_dir / "sources"
            sessions_dir = project_dir / "sessions"
            source_count = len(list(sources_dir.glob("*.md"))) if sources_dir.exists() else 0
            session_count = len(list(sessions_dir.glob("*.md"))) if sessions_dir.exists() else 0

            # Parse TODO progress
            todo_completed, todo_pending = self._count_todo_progress(project_dir)

            return ResearchProject(
                slug=slug,
                path=project_dir,
                topic=topic.strip().strip('"'),
                phase=phase,
                status=status,
                confidence=confidence,
                total_sessions=total_sessions,
                created=created,
                last_updated=last_updated,
                next_action=next_action,
                has_solution=(project_dir / "solution.md").exists(),
                has_checklist=(project_dir / "checklist.md").exists(),
                has_todo=(project_dir / "research-todo.md").exists(),
                source_count=source_count,
                session_count=session_count,
                todo_completed=todo_completed,
                todo_pending=todo_pending,
            )
        except Exception:
            logger.error("Failed to parse project: %s", project_dir, exc_info=True)
            return None

    def _count_todo_progress(self, project_dir: Path) -> tuple[int, int]:
        """Count completed and pending TODO items from research-todo.md"""
        todo_path = project_dir / "research-todo.md"
        if not todo_path.exists():
            return 0, 0
        content = todo_path.read_text(encoding="utf-8")
        completed = len(re.findall(r"^- \[x\]", content, re.MULTILINE))
        pending = len(re.findall(r"^- \[ \]", content, re.MULTILINE))
        return completed, pending

    def _extract_field(self, content: str, field_name: str) -> str | None:
        """Extract a field value from state.md markdown"""
        # Match patterns like "- field: value" or "## Field: value"
        patterns = [
            rf"- {field_name}:\s*(.+)",
            rf"## {field_name}:\s*(.+)",
            rf"^{field_name}:\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _fill_template(self, template_path: Path, variables: dict[str, str]) -> str:
        """Fill a template file with variable substitutions"""
        if not template_path.exists():
            # Fallback: use slug as placeholder
            return f"# Research Project\n\nProject initialized.\n"

        content = template_path.read_text(encoding="utf-8")
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", value)
        return content
