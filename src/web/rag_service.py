"""Reasoning-based RAG service using PageIndex for semantic report search"""

import asyncio
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_FILENAME_RE = re.compile(r"^(.+?)_(\d{6})_report\.md$")


@dataclass
class SearchResult:
    """Single search result with relevance info"""

    date: str
    filename: str
    task_name: str
    display_time: str
    relevance: float
    reasoning: str
    sections: list[dict] = field(default_factory=list)


def _import_pageindex(pageindex_path: str):
    """Import PageIndex markdown parsing functions directly from module file.

    The three needed functions (extract_nodes_from_markdown, extract_node_text_content,
    build_tree_from_nodes) are pure Python with no external dependencies.
    We mock out the heavy imports that PageIndex's utils.py requires.
    """
    import importlib.util
    import types

    pi_pkg = Path(pageindex_path) / "pageindex"
    md_module_path = pi_pkg / "page_index_md.py"
    if not md_module_path.exists():
        raise ImportError(f"PageIndex module not found: {md_module_path}")

    # The fallback import in page_index_md.py tries `from utils import *`
    # which triggers PyPDF2/pymupdf imports. We mock the utils module
    # with just what the markdown functions actually need (nothing from utils
    # is used by the three target functions).
    pi_pkg_str = str(pi_pkg)
    if pi_pkg_str not in sys.path:
        sys.path.insert(0, pi_pkg_str)

    if "utils" not in sys.modules:
        sys.modules["utils"] = types.ModuleType("utils")

    spec = importlib.util.spec_from_file_location("pageindex_md", md_module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    return (
        mod.extract_nodes_from_markdown,
        mod.extract_node_text_content,
        mod.build_tree_from_nodes,
    )


class RagService:
    """Reasoning-based RAG service powered by PageIndex"""

    def __init__(
        self,
        report_dir: Path,
        index_dir: Path,
        pageindex_path: str,
        model: str = "gpt-4o",
    ) -> None:
        self.report_dir = report_dir
        self.index_dir = index_dir
        self.pageindex_path = pageindex_path
        self.model = model
        self._index_cache: dict[str, dict] = {}
        self._available = False
        self._init_error: str = ""
        self._usage = {"search_calls": 0, "desc_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        try:
            self._extract_nodes, self._extract_text, self._build_tree = (
                _import_pageindex(pageindex_path)
            )
            self._available = True
            logger.info("PageIndex loaded from %s", pageindex_path)
        except Exception as e:
            self._init_error = f"Failed to load PageIndex: {e}"
            logger.error(self._init_error)

    @property
    def available(self) -> bool:
        return self._available

    @property
    def init_error(self) -> str:
        return self._init_error

    def build_index(self) -> int:
        """Build tree index for all reports. Returns count of indexed files."""
        if not self._available:
            return 0

        count = 0
        if not self.report_dir.is_dir():
            return 0

        for date_dir in sorted(self.report_dir.iterdir()):
            if not date_dir.is_dir() or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_dir.name):
                continue
            for report_file in sorted(date_dir.iterdir()):
                if not report_file.is_file():
                    continue
                m = _FILENAME_RE.match(report_file.name)
                if not m:
                    continue
                if self._needs_reindex(report_file, date_dir.name):
                    self._index_report(report_file, date_dir.name)
                count += 1

        self._load_index_cache()
        logger.info("Index built: %d reports", count)
        return count

    def _needs_reindex(self, report_path: Path, date: str) -> bool:
        """Check if report needs reindexing based on mtime"""
        index_path = self._index_path_for(date, report_path.stem)
        if not index_path.exists():
            return True
        return report_path.stat().st_mtime > index_path.stat().st_mtime

    def _index_path_for(self, date: str, stem: str) -> Path:
        return self.index_dir / date / f"{stem}.json"

    def _get_openai_client(self):
        """Get AsyncOpenAI client, returns None if no API key"""
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("CHATGPT_API_KEY")
        if not api_key:
            return None
        import openai

        client_kwargs: dict = {"api_key": api_key}
        base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("CHATGPT_BASE_URL")
        if base_url:
            client_kwargs["base_url"] = base_url
        return openai.AsyncOpenAI(**client_kwargs)

    def _record_usage(self, response, category: str = "search") -> None:
        """Record token usage from an OpenAI API response"""
        if hasattr(response, "usage") and response.usage:
            u = response.usage
            if category == "search":
                self._usage["search_calls"] += 1
            else:
                self._usage["desc_calls"] += 1
            self._usage["prompt_tokens"] += u.prompt_tokens or 0
            self._usage["completion_tokens"] += u.completion_tokens or 0
            self._usage["total_tokens"] += u.total_tokens or 0
            logger.info(
                "Usage [+%d tokens] %s: prompt=%d, completion=%d",
                u.total_tokens, category, u.prompt_tokens, u.completion_tokens,
            )

    def _index_report(self, report_path: Path, date: str) -> None:
        """Build tree for a single report"""
        try:
            md_content = report_path.read_text(encoding="utf-8")
            node_list, lines = self._extract_nodes(md_content)
            if not node_list:
                logger.debug("No headers found in %s, skipping", report_path.name)
                return
            nodes_with_content = self._extract_text(node_list, lines)
            tree = self._build_tree(nodes_with_content)

            m = _FILENAME_RE.match(report_path.name)
            task_name = m.group(1) if m else "unknown"
            time_str = m.group(2) if m else "000000"

            index_data = {
                "date": date,
                "filename": report_path.name,
                "task_name": task_name,
                "time_str": time_str,
                "indexed_at": datetime.now().isoformat(),
                "tree": tree,
            }

            index_path = self._index_path_for(date, report_path.stem)
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(
                json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error("Failed to index %s: %s", report_path.name, e)

    # --- Document description generation ---

    async def generate_descriptions(self) -> int:
        """Generate one-sentence descriptions for indexed docs that lack one.

        Returns count of descriptions generated.
        """
        client = self._get_openai_client()
        if not client:
            logger.warning("No API key, skipping description generation")
            return 0
        if not self._index_cache:
            self._load_index_cache()

        # Find docs without description
        pending = [
            (doc_id, data)
            for doc_id, data in self._index_cache.items()
            if not data.get("doc_description")
        ]
        if not pending:
            logger.info("All documents already have descriptions")
            return 0

        logger.info("Generating descriptions for %d documents", len(pending))

        # Concurrent with semaphore to avoid rate limits
        sem = asyncio.Semaphore(5)

        async def _gen(doc_id: str, data: dict) -> tuple[str, str]:
            async with sem:
                desc = await self._generate_single_description(client, data)
                return doc_id, desc

        results = await asyncio.gather(
            *[_gen(doc_id, data) for doc_id, data in pending],
            return_exceptions=True,
        )

        count = 0
        for r in results:
            if isinstance(r, Exception):
                logger.error("Description generation failed: %s", r)
                continue
            doc_id, desc = r
            if desc:
                self._save_description(doc_id, desc)
                count += 1

        # Reload cache with new descriptions
        self._load_index_cache()
        logger.info("Generated %d descriptions", count)
        return count

    async def _generate_single_description(self, client, data: dict) -> str:
        """Generate a one-sentence description for one document"""
        tree = data.get("tree", [])
        # Build a compact structure: titles only, no full text
        structure_str = self._extract_titles(tree, indent=0)

        prompt = f"""Generate a one-sentence description for the following document in Chinese, summarizing its main content. Make it easy to distinguish from other documents.

Task type: {data.get('task_name', 'unknown')}
Date: {data.get('date', 'unknown')}
Document structure:
{structure_str}

Return ONLY the description sentence, nothing else."""

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100,
            )
            self._record_usage(response, "desc")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Failed to generate description for %s: %s", data.get("filename"), e)
            return ""

    def _save_description(self, doc_id: str, description: str) -> None:
        """Update index file with generated description"""
        date, filename = doc_id.split("/", 1)
        stem = Path(filename).stem
        index_path = self._index_path_for(date, stem)
        if not index_path.exists():
            return
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            data["doc_description"] = description
            index_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error("Failed to save description for %s: %s", doc_id, e)

    def _load_index_cache(self) -> None:
        """Load all index files into memory cache"""
        self._index_cache.clear()
        if not self.index_dir.is_dir():
            return
        for date_dir in sorted(self.index_dir.iterdir()):
            if not date_dir.is_dir():
                continue
            for idx_file in date_dir.glob("*.json"):
                try:
                    data = json.loads(idx_file.read_text(encoding="utf-8"))
                    doc_id = f"{data['date']}/{data['filename']}"
                    self._index_cache[doc_id] = data
                except Exception as e:
                    logger.error("Failed to load index %s: %s", idx_file, e)

    def _build_catalog(self) -> str:
        """Build compact catalog of all indexed trees for LLM consumption"""
        if not self._index_cache:
            self._load_index_cache()

        entries = []
        for doc_id, data in self._index_cache.items():
            tree = data.get("tree", [])
            titles = self._extract_titles(tree, indent=0)
            desc = data.get("doc_description", "")
            desc_line = f"\n  Summary: {desc}" if desc else ""
            entries.append(
                f"[{doc_id}] task: {data['task_name']}, date: {data['date']}{desc_line}\n{titles}"
            )
        return "\n\n".join(entries)

    def _extract_titles(self, nodes: list[dict], indent: int = 0) -> str:
        """Extract hierarchical titles from tree nodes"""
        lines = []
        prefix = "  " * indent
        for node in nodes:
            title = node.get("title", "")
            node_id = node.get("node_id", "")
            lines.append(f"{prefix}- [{node_id}] {title}")
            children = node.get("nodes", [])
            if children:
                lines.append(self._extract_titles(children, indent + 1))
        return "\n".join(lines)

    def _extract_text_for_nodes(self, tree: list[dict], node_ids: list[str]) -> list[dict]:
        """Extract text content for specific node_ids from a tree"""
        results = []
        all_nodes = self._flatten_tree(tree)
        for node in all_nodes:
            if node.get("node_id", "") in node_ids:
                text = node.get("text", "")
                results.append({
                    "title": node.get("title", ""),
                    "node_id": node.get("node_id", ""),
                    "snippet": text[:500] + ("..." if len(text) > 500 else ""),
                })
        return results

    def _flatten_tree(self, nodes: list[dict]) -> list[dict]:
        """Flatten tree into a list of all nodes"""
        result = []
        for node in nodes:
            result.append(node)
            children = node.get("nodes", [])
            if children:
                result.extend(self._flatten_tree(children))
        return result

    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Search reports using LLM reasoning over tree structures"""
        if not self._available:
            raise RuntimeError("RAG service not available: " + self._init_error)

        client = self._get_openai_client()
        if not client:
            raise RuntimeError("OPENAI_API_KEY or CHATGPT_API_KEY not set")

        catalog = self._build_catalog()
        if not catalog:
            return []

        prompt = self._build_search_prompt(query, catalog)

        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content
        self._record_usage(response, "search")

        return self._parse_search_response(content, top_k)

    def _build_search_prompt(self, query: str, catalog: str) -> str:
        return f"""You are an intelligent document retrieval assistant. Given a user query and a catalog of document tree structures, find all documents that are relevant to the query.

For each relevant document, explain briefly why it is relevant and assign a relevance score from 0.0 to 1.0.

User Query: {query}

Document Catalog (format: [date/filename] metadata, followed by section tree):
{catalog}

Reply in the following JSON format only:
```json
{{
  "thinking": "Your reasoning about the query and which documents are relevant",
  "results": [
    {{
      "doc_id": "date/filename",
      "reason": "Brief explanation of relevance",
      "relevance": 0.9,
      "relevant_node_ids": ["0001", "0003"]
    }}
  ]
}}
```"""

    def _parse_search_response(self, content: str, top_k: int) -> list[SearchResult]:
        """Parse LLM search response into SearchResult list"""
        try:
            # Extract JSON from response
            json_str = content
            if "```json" in json_str:
                json_str = json_str.split("```json", 1)[1]
            if "```" in json_str:
                json_str = json_str.split("```", 1)[0]
            json_str = json_str.strip()

            data = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error("Failed to parse search response: %s", e)
            return []

        results = []
        for item in data.get("results", [])[:top_k]:
            doc_id = item.get("doc_id", "")
            idx_data = self._index_cache.get(doc_id)
            if not idx_data:
                continue

            time_str = idx_data.get("time_str", "000000")
            display_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

            node_ids = item.get("relevant_node_ids", [])
            sections = self._extract_text_for_nodes(idx_data.get("tree", []), node_ids)

            results.append(
                SearchResult(
                    date=idx_data["date"],
                    filename=idx_data["filename"],
                    task_name=idx_data["task_name"],
                    display_time=display_time,
                    relevance=item.get("relevance", 0.5),
                    reasoning=item.get("reason", ""),
                    sections=sections,
                )
            )

        results.sort(key=lambda r: r.relevance, reverse=True)
        return results

    def get_status(self) -> dict:
        """Return index status"""
        if not self._index_cache:
            self._load_index_cache()
        with_desc = sum(1 for d in self._index_cache.values() if d.get("doc_description"))
        return {
            "available": self._available,
            "error": self._init_error if not self._available else "",
            "total_docs": len(self._index_cache),
            "docs_with_description": with_desc,
            "usage": self._usage,
            "index_dir": str(self.index_dir),
        }
