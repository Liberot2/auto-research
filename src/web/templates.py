"""HTML templates for the report viewer"""

_CSS = """
:root {
    --bg: #f8f9fa;
    --surface: #ffffff;
    --text: #1a1a2e;
    --text-secondary: #555;
    --border: #e2e8f0;
    --accent: #4f46e5;
    --accent-hover: #4338ca;
    --accent-light: #eef2ff;
    --sidebar-bg: #ffffff;
    --muted: #8896a6;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
    --radius: 8px;
    --green: #10b981;
    --blue: #3b82f6;
    --orange: #f59e0b;
    --purple: #8b5cf6;
    --pink: #ec4899;
    --red: #ef4444;
}
:root[data-theme='dark'] {
    --bg: #0f1117;
    --surface: #1a1d27;
    --text: #e2e8f0;
    --text-secondary: #94a3b8;
    --border: #2d3348;
    --accent: #818cf8;
    --accent-hover: #6366f1;
    --accent-light: #1e1b4b;
    --sidebar-bg: #1a1d27;
    --muted: #64748b;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.2);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.4);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.layout {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

/* Sidebar */
.sidebar {
    width: 280px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    padding: 0;
    overflow-y: auto;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
}
.sidebar-brand {
    padding: 24px 20px 16px;
    border-bottom: 1px solid var(--border);
}
.sidebar-brand h1 {
    font-size: 18px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.3px;
}
.sidebar-brand p {
    font-size: 12px;
    color: var(--muted);
    margin-top: 2px;
}
.sidebar-section {
    padding: 16px 12px;
}
.sidebar-section-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 0 8px 8px;
}
.sidebar ul { list-style: none; }
.sidebar li { margin-bottom: 2px; }
.sidebar li a {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    color: var(--text);
    transition: background 0.15s, color 0.15s;
}
.sidebar li a:hover {
    background: var(--accent-light);
    text-decoration: none;
}
.sidebar li a.active {
    background: var(--accent);
    color: #fff;
    font-weight: 500;
}
.sidebar li a .count {
    font-size: 12px;
    opacity: 0.7;
    min-width: 20px;
    text-align: center;
}
.sidebar li a.active .count { opacity: 0.9; }
.sidebar-footer {
    margin-top: auto;
    padding: 12px;
    border-top: 1px solid var(--border);
}

/* Main content */
.main {
    flex: 1;
    padding: 32px 40px;
    min-width: 0;
    overflow-y: auto;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 28px;
}
.header h1 {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.3px;
}
.theme-btn {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 7px 14px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-secondary);
    transition: border-color 0.15s, box-shadow 0.15s;
    box-shadow: var(--shadow-sm);
}
.theme-btn:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow-md);
}

/* Cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 22px;
    margin-bottom: 10px;
    transition: box-shadow 0.2s, transform 0.15s, border-color 0.15s;
    box-shadow: var(--shadow-sm);
}
.card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--accent);
    transform: translateY(-1px);
}
.card-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.card-icon {
    width: 38px;
    height: 38px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    color: #fff;
    font-weight: 700;
}
.card-body { flex: 1; }
.card-title {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 4px;
}
.card-title a {
    color: var(--text);
}
.card-title a:hover {
    color: var(--accent);
    text-decoration: none;
}
.card-meta {
    font-size: 13px;
    color: var(--muted);
}

/* Task type colors */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-morning_papers { background: #fef3c7; color: #92400e; }
.badge-site_monitor { background: #dbeafe; color: #1e40af; }
.badge-daily_report { background: #d1fae5; color: #065f46; }
.badge-github_agent_trend { background: #ede9fe; color: #5b21b6; }
.badge-default { background: var(--accent-light); color: var(--accent); }

:root[data-theme='dark'] .badge-morning_papers { background: #78350f; color: #fde68a; }
:root[data-theme='dark'] .badge-site_monitor { background: #1e3a5f; color: #93c5fd; }
:root[data-theme='dark'] .badge-daily_report { background: #064e3b; color: #6ee7b7; }
:root[data-theme='dark'] .badge-github_agent_trend { background: #4c1d95; color: #c4b5fd; }
:root[data-theme='dark'] .badge-default { background: var(--accent-light); color: var(--accent); }

/* Search bar */
.search-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
}
.search-bar input {
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 14px;
    background: var(--surface);
    color: var(--text);
    flex: 1;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.15s, box-shadow 0.15s;
}
.search-bar input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-light);
}
.search-bar select {
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 14px;
    background: var(--surface);
    color: var(--text);
    min-width: 140px;
}
.search-bar button {
    padding: 10px 20px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background 0.15s;
}
.search-bar button:hover { background: var(--accent-hover); }

/* Filter bar */
.filter-bar {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    align-items: center;
    flex-wrap: wrap;
}
.filter-bar select {
    padding: 7px 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 13px;
    background: var(--surface);
    color: var(--text);
    box-shadow: var(--shadow-sm);
}
.filter-link {
    font-size: 13px;
    color: var(--accent);
    padding: 7px 12px;
    border-radius: var(--radius);
    transition: background 0.15s;
}
.filter-link:hover {
    background: var(--accent-light);
    text-decoration: none;
}

/* Report content */
.report-content {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 36px 44px;
    box-shadow: var(--shadow-sm);
    line-height: 1.85;
}
.report-content h1 {
    font-size: 26px;
    font-weight: 700;
    margin: 32px 0 16px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--border);
    letter-spacing: -0.3px;
}
.report-content h1:first-child { margin-top: 0; }
.report-content h2 {
    font-size: 22px;
    font-weight: 600;
    margin: 28px 0 14px;
    letter-spacing: -0.2px;
}
.report-content h3 {
    font-size: 18px;
    font-weight: 600;
    margin: 22px 0 10px;
}
.report-content p { margin-bottom: 14px; }
.report-content ul, .report-content ol { margin: 10px 0 14px 28px; }
.report-content li { margin-bottom: 6px; }
.report-content blockquote {
    border-left: 3px solid var(--accent);
    padding: 12px 20px;
    margin: 16px 0;
    background: var(--accent-light);
    border-radius: 0 6px 6px 0;
}
.report-content code {
    background: var(--accent-light);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 0.88em;
}
.report-content pre {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 18px;
    border-radius: var(--radius);
    overflow-x: auto;
    margin: 16px 0;
}
.report-content pre code { background: none; padding: 0; }
.report-content table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
}
.report-content th, .report-content td {
    border: 1px solid var(--border);
    padding: 10px 14px;
    text-align: left;
}
.report-content th { background: var(--accent-light); font-weight: 600; }
.report-content hr { border: none; border-top: 1px solid var(--border); margin: 20px 0; }
.report-content img { max-width: 100%; border-radius: var(--radius); }
.report-content strong { font-weight: 600; }
.report-content { word-wrap: break-word; overflow-wrap: break-word; }

/* Back link */
.back-link {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 20px;
    font-size: 14px;
    color: var(--muted);
    padding: 6px 12px;
    border-radius: 6px;
    transition: color 0.15s, background 0.15s;
}
.back-link:hover {
    color: var(--accent);
    background: var(--accent-light);
    text-decoration: none;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
}
.empty-state p { font-size: 16px; }
"""

_JS = """
<script>
(function() {{
    var t = localStorage.getItem('report-theme') || 'light';
    document.documentElement.setAttribute('data-theme', t);
}})();
function toggleTheme() {{
    var cur = document.documentElement.getAttribute('data-theme');
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('report-theme', next);
}}
</script>
"""

_TASK_ICONS: dict[str, tuple[str, str]] = {
    "morning_papers": ("M", "#f59e0b"),
    "site_monitor": ("S", "#3b82f6"),
    "daily_report": ("D", "#10b981"),
    "github_agent_trend": ("G", "#8b5cf6"),
}

_BADGE_CLASSES: dict[str, str] = {
    "morning_papers": "badge-morning_papers",
    "site_monitor": "badge-site_monitor",
    "daily_report": "badge-daily_report",
    "github_agent_trend": "badge-github_agent_trend",
}


def _task_icon(task_name: str) -> tuple[str, str]:
    return _TASK_ICONS.get(task_name, (task_name[0].upper(), "#6b7280"))


def _badge_class(task_name: str) -> str:
    return _BADGE_CLASSES.get(task_name, "badge-default")


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Report Viewer</title>
<style>{_CSS}</style>
</head>
<body>
{_JS}
{body}
</body>
</html>"""


def _sidebar(
    dates: list[str],
    active_date: str = "",
    date_counts: dict[str, int] | None = None,
) -> str:
    date_counts = date_counts or {}
    items = []
    for d in dates:
        cls = ' class="active"' if d == active_date else ""
        cnt = date_counts.get(d, 0)
        count_html = f'<span class="count">{cnt}</span>' if cnt else ""
        items.append(f'<li><a href="/date/{d}"{cls}>{d}{count_html}</a></li>')
    date_list = "\n".join(items) if items else "<li>No dates</li>"
    return f"""
<div class="sidebar">
    <div class="sidebar-brand">
        <h1>Report Viewer</h1>
        <p>Auto Research Reports</p>
    </div>
    <div class="sidebar-section">
        <div class="sidebar-section-title">Dates</div>
        <ul>{date_list}</ul>
    </div>
    <div class="sidebar-footer">
        <button class="theme-btn" onclick="toggleTheme()" style="width:100%">Toggle Theme</button>
    </div>
</div>"""


def _render_card(r: dict) -> str:
    letter, color = _task_icon(r["task_name"])
    badge_cls = _badge_class(r["task_name"])
    return f"""<a href="/report/{r['date']}/{r['filename']}" style="text-decoration:none;color:inherit">
<div class="card">
    <div class="card-row">
        <div class="card-icon" style="background:{color}">{letter}</div>
        <div class="card-body">
            <div class="card-title"><a href="/report/{r['date']}/{r['filename']}">{r['task_name']}</a></div>
            <div class="card-meta">
                <span class="badge {badge_cls}">{r['task_name']}</span>
                &nbsp;&middot;&nbsp; {r['display_time']} &middot; {r['date']}
            </div>
        </div>
    </div>
</div></a>"""


def render_index(
    dates: list[str],
    latest_date: str,
    reports: list[dict],
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the index page showing latest date reports"""
    cards = [_render_card(r) for r in reports]
    report_cards = "\n".join(cards) if cards else '<div class="empty-state"><p>No reports found</p></div>'
    body = f"""
<div class="layout">
{_sidebar(dates, active_date=latest_date, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>Reports &mdash; {latest_date}</h1>
    </div>
    <div class="filter-bar">
        <a href="/search" class="filter-link">Search Reports</a>
    </div>
    {report_cards}
</div>
</div>"""
    return _page("Reports", body)


def render_date(
    dates: list[str],
    date: str,
    reports: list[dict],
    task_types: list[str],
    current_type: str = "",
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render a date page with task type filter"""
    filter_options = ['<option value="">All Tasks</option>']
    for t in task_types:
        sel = ' selected' if t == current_type else ""
        filter_options.append(f'<option value="{t}"{sel}>{t}</option>')
    cards = [_render_card(r) for r in reports]
    report_cards = "\n".join(cards) if cards else '<div class="empty-state"><p>No reports for this date</p></div>'
    body = f"""
<div class="layout">
{_sidebar(dates, active_date=date, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>Reports &mdash; {date}</h1>
    </div>
    <div class="filter-bar">
        <form method="get" action="/date/{date}" style="display:flex;gap:8px">
            <select name="task_type" onchange="this.form.submit()">
                {"".join(filter_options)}
            </select>
        </form>
        <a href="/search" class="filter-link">Search</a>
    </div>
    {report_cards}
</div>
</div>"""
    return _page(f"Reports - {date}", body)


def render_report(
    dates: list[str],
    date: str,
    filename: str,
    title: str,
    html_content: str,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render a single report with markdown content"""
    body = f"""
<div class="layout">
{_sidebar(dates, active_date=date, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>{title}</h1>
    </div>
    <a href="/date/{date}" class="back-link">&larr; {date}</a>
    <div class="report-content">{html_content}</div>
</div>
</div>"""
    return _page(title, body)


def render_search(
    dates: list[str],
    query: str = "",
    task_types: list[str] | None = None,
    current_type: str = "",
    current_date: str = "",
    results: list[dict] | None = None,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the search page"""
    task_types = task_types or []
    results = results or []
    type_options = ['<option value="">All Tasks</option>']
    for t in task_types:
        sel = ' selected' if t == current_type else ""
        type_options.append(f'<option value="{t}"{sel}>{t}</option>')
    date_options = ['<option value="">All Dates</option>']
    for d in dates:
        sel = ' selected' if d == current_date else ""
        date_options.append(f'<option value="{d}"{sel}>{d}</option>')
    cards = [_render_card(r) for r in results]
    result_section = "\n".join(cards) if cards else ""
    if query and not results:
        result_section = '<div class="empty-state"><p>No results found</p></div>'
    body = f"""
<div class="layout">
{_sidebar(dates, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>Search Reports</h1>
    </div>
    <form class="search-bar" method="get" action="/search">
        <input type="text" name="q" value="{query}" placeholder="Search reports...">
        <select name="task_type">
            {"".join(type_options)}
        </select>
        <select name="date">
            {"".join(date_options)}
        </select>
        <button type="submit">Search</button>
    </form>
    {result_section}
</div>
</div>"""
    return _page("Search", body)


def render_error(
    dates: list[str],
    message: str,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render an error page"""
    body = f"""
<div class="layout">
{_sidebar(dates, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>Error</h1>
    </div>
    <div class="empty-state"><p>{message}</p></div>
</div>
</div>"""
    return _page("Error", body)
