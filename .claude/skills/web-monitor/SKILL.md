---
name: web-monitor
description: |
  Monitor specified websites for content changes, accessibility status, and generate summary reports.
  Use when the user wants to: (1) Check if websites are accessible, (2) Monitor web page content changes,
  (3) Track website updates on a schedule, (4) Get website status reports.
  Triggers: "web monitor", "网站监控", "monitor website", "check url", "网页变化", "site status".
---

# Web Monitor

Monitor websites for accessibility and content changes.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `urls` | array | `[]` | List of URLs to monitor |
| `report_path` | string | _(auto)_ | Report save path, injected by runner |

## Workflow

1. **Validate**: For each URL in `urls`, verify accessibility using WebSearch or by attempting to fetch the page content.
2. **Summarize**: For accessible pages, extract and summarize key content (headings, main topics, recent updates).
3. **Compare**: If previous monitoring data exists (check previous day's `_report.md` in the same date-based log directory), highlight notable changes.
4. **Report**: Generate a monitoring report with status for each URL.
5. **Save**: Save the report to the file path specified by `report_path`.

## Output Format

```markdown
## 网页监控报告
**检查时间**: {timestamp}

### {URL}
- **状态**: 可访问 / 不可访问
- **状态码**: {status_code}
- **内容摘要**: {summary}
- **变化检测**: {changes_if_any}
```

## Notes

- Report output in Chinese (中文)
- For URLs that fail to access, include error details
- Keep summaries concise (2-3 sentences per URL)
