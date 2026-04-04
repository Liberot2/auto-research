---
name: daily-summary
description: |
  Analyze a project directory's recent changes and generate a daily work summary report.
  Use when the user wants to: (1) Get a daily standup summary, (2) Review project changes,
  (3) Generate work reports, (4) Analyze git commit history, (5) Track project progress.
  Triggers: "daily summary", "日报", "工作摘要", "每日总结", "project report", "standup",
  "changelog", "git summary", "变更分析".
---

# Daily Summary

Generate daily work summaries from project directory analysis.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_dir` | string | `.` | Project directory to analyze |

## Workflow

1. **Scan directory**: Use Glob to list project structure, identify main components.
2. **Git history**: If a git repo, run `git log --oneline -10` and `git diff --stat HEAD~5..HEAD` to get recent activity.
3. **Recent files**: Use `git status` or check file modification times to find recently changed files.
4. **Analyze changes**: Read key changed files to understand what was modified and why.
5. **Generate report**: Create a structured daily summary.

## Output Format

```markdown
## 每日工作摘要
**日期**: {date}
**项目目录**: {target_dir}

### 项目概况
{project_overview}

### 近期变更
{recent_changes}

### 关键提交
{key_commits}

### 建议与总结
{suggestions}
```

## Notes

- Report in Chinese (中文)
- Focus on substantive changes, skip trivial file modifications
- If not a git repo, rely on file modification times instead
- Keep the report concise and actionable
