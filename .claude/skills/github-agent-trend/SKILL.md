---
name: github-agent-trend
description: |
  Fetch trending projects from GitHub related to specified topics (default: AI Agent),
  extract core innovations and highlights for each project.
  Use when the user wants to: (1) Track trending Agent/AI projects on GitHub,
  (2) Discover new open-source agent frameworks and tools,
  (3) Get a digest of hot agent-related repositories,
  (4) Monitor GitHub trending for specific tech topics.
  Triggers: "github trend", "agent trend", "GitHub趋势", "开源Agent", "trending repos",
  "热门项目", "github trending", "agent开源".
---

# GitHub Agent Trend Tracker

Fetch GitHub Trending projects filtered by topic, extract core innovations and generate a structured highlights report.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | `"agent"` | Topic keyword to filter trending repositories |
| `max_repos` | integer | `10` | Maximum number of repositories to include in report |
| `language` | string | `""` | Programming language filter (empty string = all languages) |

## Workflow

1. **Fetch Trending**: Use WebSearch to access GitHub Trending page. Query patterns:
   - `github.com/trending` — general trending repos
   - If `language` is specified: `github.com/trending/{language}?since=daily`
   - Also search: `"github trending" {topic} {date}` to capture discussion and curated lists

2. **Filter by Topic**: From the fetched trending list, select repositories relevant to `topic`. Match against:
   - Repository name and description
   - Topic tags (e.g., `agent`, `ai-agent`, `llm`, `autonomous-agent`)
   - README keywords (if accessible)
   - Exclude repos that are only tangentially related

3. **Enrich Details**: For each filtered repository, gather:
   - Star count and recent growth (compare with search results or cached data)
   - Primary language and tech stack
   - Last commit activity (recent = actively maintained)
   - Brief description of what it does
   Use WebSearch with query: `github.com/{owner}/{repo}` and `site:github.com {repo_name}`

4. **Extract Highlights**: For each project, identify:
   - Core innovation: What makes this project unique or notable?
   - Problem solved: What real-world problem does it address?
   - Key differentiator: How does it compare to existing alternatives?
   - Notable features: Standout capabilities or design choices

5. **Report**: Generate a structured markdown report in Chinese with the following sections:
   - Executive summary (overview of trends observed)
   - Project highlights (one section per repo with structured info)
   - Trend analysis (common patterns, emerging directions)

## Output Language

- Report body: Chinese (中文)
- Repository names, URLs, and technical terms: Preserve original English
- Code examples or command-line snippets: Keep in English

## Search Tips

- GitHub Trending page updates daily, use `since=daily` or `since=weekly` parameter
- Supplement with Google/Reddit discussions for context: `"github trending agent" site:reddit.com`
- When stars count is ambiguous, prefer the number from the GitHub page itself
- If fewer than `max_repos` repos match the topic, include only genuine matches rather than padding

## Output Format

```markdown
## GitHub Agent 趋势报告

**抓取时间**: {timestamp}
**筛选主题**: {topic}
**筛选语言**: {language or 全部}

### 趋势概览
{2-3 sentence summary of overall trends}

---

### 1. {project_name}
- **仓库**: {repo_url}
- **Stars**: {star_count}
- **语言**: {primary_language}
- **最近活跃**: {last_activity}

**核心亮点**: {1-2 sentences on what makes this project innovative}

**解决问题**: {What problem does it solve}

**关键特性**:
- {feature_1}
- {feature_2}

---

### 趋势分析
{Common patterns, emerging directions across all projects}
```
