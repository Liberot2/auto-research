---
name: arxiv-tracker
description: |
  Search and track latest academic papers on ArXiv by keywords, generating structured summary reports.
  Use when the user wants to: (1) Find recent papers on specific research topics,
  (2) Track academic publications in AI/ML/NLP fields, (3) Generate literature survey reports,
  (4) Get daily/weekly paper digest. Triggers: "arxiv", "papers", "论文", "paper tracker",
  "literature review", "paper search", "论文追踪", "最新论文".
---

# ArXiv Paper Tracker

Track and summarize latest academic papers on specified research topics.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keywords` | array | `["large language model"]` | Search keywords for paper discovery |
| `max_papers` | integer | `5` | Maximum number of papers to include |

## Workflow

1. **Search**: For each keyword in `keywords`, use WebSearch to find recent ArXiv papers (focus on last 30 days). Query pattern: `site:arxiv.org <keyword> 2025` or `site:arxiv.org <keyword> recent`.
2. **Filter**: Select up to `max_papers` most relevant and impactful papers. Prioritize papers with high citation potential or novel contributions.
3. **Extract**: For each paper, extract: title (original English), authors, submission date, core contribution (2-3 sentences), key methods/techniques.
4. **Analyze**: Identify common themes, emerging trends, and methodological patterns across papers.
5. **Report**: Generate a structured markdown report following the template at `assets/report-template.md`.

## Output Language

- Report body: Chinese (中文)
- Paper titles and author names: Preserve original English
- Technical terms: Keep English in parentheses after Chinese translation

## Search Tips

- Use multiple query variations for each keyword to maximize coverage
- Include both broad terms ("transformer") and specific terms ("attention mechanism")
- Check both arxiv.org and ar5iv.org for better abstract access
