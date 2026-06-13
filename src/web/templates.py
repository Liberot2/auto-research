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
.card-actions {
    display: flex;
    gap: 6px;
    align-items: center;
    flex-shrink: 0;
    align-self: center;
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
.badge-research { background: #fce7f3; color: #9d174d; }
.badge-default { background: var(--accent-light); color: var(--accent); }
.badge-enabled { background: #d1fae5; color: #065f46; }
.badge-disabled { background: #fee2e2; color: #991b1b; }
.badge-success { background: #d1fae5; color: #065f46; }
.badge-failed { background: #fee2e2; color: #991b1b; }

:root[data-theme='dark'] .badge-morning_papers { background: #78350f; color: #fde68a; }
:root[data-theme='dark'] .badge-site_monitor { background: #1e3a5f; color: #93c5fd; }
:root[data-theme='dark'] .badge-daily_report { background: #064e3b; color: #6ee7b7; }
:root[data-theme='dark'] .badge-github_agent_trend { background: #4c1d95; color: #c4b5fd; }
:root[data-theme='dark'] .badge-research { background: #831843; color: #f9a8d4; }
:root[data-theme='dark'] .badge-default { background: var(--accent-light); color: var(--accent); }
:root[data-theme='dark'] .badge-enabled { background: #064e3b; color: #6ee7b7; }
:root[data-theme='dark'] .badge-disabled { background: #7f1d1d; color: #fca5a5; }
:root[data-theme='dark'] .badge-success { background: #064e3b; color: #6ee7b7; }
:root[data-theme='dark'] .badge-failed { background: #7f1d1d; color: #fca5a5; }

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

/* Action bar (download/bookmark on report page) */
.action-bar {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 16px;
}
.action-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 13px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
    text-decoration: none;
}
.action-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    text-decoration: none;
}

/* Run button */
.run-btn {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: background 0.15s, opacity 0.15s;
}
.run-btn:hover { background: var(--accent-hover); }
.run-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.run-btn.running { background: var(--orange); }

/* Toggle button */
.toggle-btn {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 14px;
    cursor: pointer;
    font-size: 13px;
    transition: border-color 0.15s;
}
.toggle-btn:hover { border-color: var(--accent); }

/* Compare view */
.compare-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 20px;
}
.compare-pane {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    overflow-x: auto;
    max-height: 70vh;
    overflow-y: auto;
}
.compare-pane h3 {
    font-size: 14px;
    color: var(--muted);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}
.diff-add { background: #d1fae5; }
.diff-remove { background: #fee2e2; }
.diff-context { background: transparent; }
:root[data-theme='dark'] .diff-add { background: #064e3b; }
:root[data-theme='dark'] .diff-remove { background: #7f1d1d; }
.diff-line {
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 12px;
    line-height: 1.6;
    padding: 1px 8px;
    white-space: pre-wrap;
    word-break: break-all;
}

/* Bookmark star */
.bookmark-star {
    cursor: pointer;
    font-size: 18px;
    color: var(--muted);
    transition: color 0.15s;
    background: none;
    border: none;
    padding: 4px;
}
.bookmark-star.active { color: #f59e0b; }
.bookmark-star:hover { color: #f59e0b; }

/* Ask / semantic search */
.ask-container {
    max-width: 860px;
}
.ask-input-wrap {
    display: flex;
    gap: 10px;
    margin-bottom: 28px;
    align-items: flex-end;
}
.ask-input-wrap textarea {
    flex: 1;
    min-height: 52px;
    max-height: 200px;
    padding: 12px 16px;
    border: 2px solid var(--border);
    border-radius: var(--radius);
    font-size: 15px;
    background: var(--surface);
    color: var(--text);
    resize: vertical;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.15s, box-shadow 0.15s;
    font-family: inherit;
    line-height: 1.5;
}
.ask-input-wrap textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-light);
}
.ask-submit {
    padding: 12px 24px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background 0.15s, opacity 0.15s;
    white-space: nowrap;
    height: 48px;
}
.ask-submit:hover { background: var(--accent-hover); }
.ask-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.ask-error {
    background: #fee2e2;
    color: #991b1b;
    padding: 12px 16px;
    border-radius: var(--radius);
    margin-bottom: 16px;
    font-size: 14px;
}
:root[data-theme='dark'] .ask-error { background: #7f1d1d; color: #fca5a5; }
.ask-result-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-sm);
    transition: border-color 0.15s, box-shadow 0.15s;
}
.ask-result-card:hover { border-color: var(--accent); box-shadow: var(--shadow-md); }
.ask-result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}
.ask-result-title {
    font-size: 16px;
    font-weight: 600;
}
.ask-result-title a { color: var(--text); }
.ask-result-title a:hover { color: var(--accent); text-decoration: none; }
.relevance-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}
.relevance-high { background: #dcfce7; color: #166534; }
.relevance-med { background: var(--accent-light); color: var(--accent); }
.relevance-low { background: #fef3c7; color: #92400e; }
:root[data-theme='dark'] .relevance-high { background: #052e16; color: #86efac; }
:root[data-theme='dark'] .relevance-med { background: #1e1b4b; color: #a5b4fc; }
:root[data-theme='dark'] .relevance-low { background: #451a03; color: #fcd34d; }
.ask-reasoning {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 10px 0;
    padding: 10px 14px;
    background: var(--bg);
    border-radius: 6px;
    line-height: 1.6;
    border-left: 3px solid var(--accent);
}
.ask-snippets {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.ask-snippet {
    font-size: 13px;
    color: var(--text-secondary);
    padding: 8px 12px;
    border-left: 3px solid var(--border);
    background: var(--bg);
    border-radius: 0 6px 6px 0;
    line-height: 1.5;
}
.ask-snippet-title {
    font-weight: 600;
    color: var(--text);
    font-size: 12px;
    margin-bottom: 3px;
}
.ask-status {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    font-size: 13px;
    color: var(--muted);
}
.ask-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}
.ask-status-dot.active { background: var(--green); }
.ask-status-dot.inactive { background: var(--red); }
.ask-loading {
    text-align: center;
    padding: 48px;
    color: var(--muted);
    font-size: 15px;
}

/* Log viewer */
.log-header {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}
.log-stat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 16px;
    text-align: center;
}
.log-stat .label { font-size: 12px; color: var(--muted); margin-bottom: 4px; }
.log-stat .value { font-size: 18px; font-weight: 600; }
.log-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-bottom: 16px;
}
.log-section-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}
.log-section pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-all;
}

/* Config block */
.config-grid {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px 16px;
    font-size: 14px;
}
.config-key { font-weight: 600; color: var(--muted); }
.config-val { color: var(--text); }

/* History table */
.history-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
.history-table th, .history-table td {
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
}
.history-table th {
    font-weight: 600;
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.history-table tr:hover { background: var(--accent-light); }

/* Compare form */
.compare-form {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
}
.compare-col h3 {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
.compare-col select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 13px;
    background: var(--surface);
    color: var(--text);
    margin-bottom: 8px;
}

/* Phase progress bar */
.phase-progress {
    display: flex;
    align-items: flex-start;
    gap: 0;
    margin: 12px 0;
    position: relative;
}
.phase-step {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
}
.phase-step .phase-dot {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid var(--border);
    background: var(--surface);
    margin-bottom: 6px;
    position: relative;
    z-index: 1;
}
.phase-step .phase-label {
    font-size: 11px;
    color: var(--muted);
    text-align: center;
    white-space: nowrap;
}
.phase-step-done .phase-dot {
    background: var(--phase-color);
    border-color: var(--phase-color);
}
.phase-step-done .phase-label {
    color: var(--text-secondary);
}
.phase-step-active .phase-dot {
    background: var(--phase-color);
    border-color: var(--phase-color);
    box-shadow: 0 0 0 4px color-mix(in srgb, var(--phase-color) 25%, transparent);
}
.phase-step-active .phase-label {
    color: var(--text);
    font-weight: 600;
}
.phase-step:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 8px;
    left: calc(50% + 12px);
    width: calc(100% - 24px);
    height: 2px;
    background: var(--border);
}
.phase-step-done:not(:last-child)::after {
    background: var(--phase-color);
}
"""

_JS = """
<script>
(function() {
    var t = localStorage.getItem('report-theme') || 'light';
    document.documentElement.setAttribute('data-theme', t);
})();
function toggleTheme() {
    var cur = document.documentElement.getAttribute('data-theme');
    var next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('report-theme', next);
}
async function runTask(taskName, btn) {
    btn.disabled = true;
    var orig = btn.textContent;
    btn.textContent = 'Running...';
    btn.classList.add('running');
    try {
        var resp = await fetch('/api/tasks/' + taskName + '/run', {method: 'POST'});
        var data = await resp.json();
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Task "' + taskName + '" started');
        }
    } catch(e) {
        alert('Request failed: ' + e.message);
    }
    btn.disabled = false;
    btn.textContent = orig;
    btn.classList.remove('running');
}
async function toggleTask(taskName) {
    try {
        var resp = await fetch('/api/tasks/' + taskName + '/toggle', {method: 'POST'});
        var data = await resp.json();
        location.reload();
    } catch(e) {
        alert('Toggle failed: ' + e.message);
    }
}
async function toggleBookmark(date, filename, starEl) {
    var isBookmarked = starEl.classList.contains('active');
    var method = isBookmarked ? 'DELETE' : 'POST';
    try {
        var resp = await fetch('/api/bookmarks', {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({date: date, filename: filename})
        });
        if (resp.ok) {
            starEl.classList.toggle('active');
            starEl.textContent = isBookmarked ? '\\u2606' : '\\u2605';
        }
    } catch(e) {}
}
async function askQuery(btn) {
    var input = document.getElementById('ask-input');
    var resultsDiv = document.getElementById('ask-results');
    var query = input.value.trim();
    if (!query) return;
    btn.disabled = true;
    btn.textContent = 'Thinking...';
    resultsDiv.innerHTML = '<div class="ask-loading">Searching reports...</div>';
    try {
        var resp = await fetch('/api/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        });
        var data = await resp.json();
        if (data.error) {
            resultsDiv.innerHTML = '<div class="ask-error">' + data.error + '</div>';
        } else {
            renderAskResults(data.results, resultsDiv);
        }
    } catch(e) {
        resultsDiv.innerHTML = '<div class="ask-error">Request failed: ' + e.message + '</div>';
    }
    btn.disabled = false;
    btn.textContent = 'Search';
}
document.getElementById('ask-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        var btn = document.querySelector('.ask-submit');
        if (btn && !btn.disabled) askQuery(btn);
    }
});
function renderAskResults(results, container) {
    if (!results.length) {
        container.innerHTML = '<div class="empty-state"><p>No relevant reports found</p></div>';
        return;
    }
    var html = '';
    for (var i = 0; i < results.length; i++) {
        var r = results[i];
        var pct = Math.round(r.relevance * 100);
        var relCls = pct >= 70 ? 'relevance-high' : pct >= 40 ? 'relevance-med' : 'relevance-low';
        html += '<div class="ask-result-card">';
        html += '<div class="ask-result-header">';
        html += '<div class="ask-result-title"><a href="/report/' + r.date + '/' + r.filename + '">' + escHtml(r.task_name) + ' &mdash; ' + escHtml(r.display_time) + '</a></div>';
        html += '<span class="relevance-badge ' + relCls + '">' + pct + '% match</span>';
        html += '</div>';
        html += '<div class="card-meta"><span class="badge ' + badgeClass(r.task_name) + '">' + escHtml(r.task_name) + '</span> &middot; ' + r.date + '</div>';
        if (r.reasoning) {
            html += '<div class="ask-reasoning">' + escHtml(r.reasoning) + '</div>';
        }
        if (r.sections && r.sections.length) {
            html += '<div class="ask-snippets">';
            for (var j = 0; j < r.sections.length; j++) {
                var s = r.sections[j];
                html += '<div class="ask-snippet">';
                html += '<div class="ask-snippet-title">' + escHtml(s.title) + '</div>';
                html += escHtml(s.snippet);
                html += '</div>';
            }
            html += '</div>';
        }
        html += '</div>';
    }
    container.innerHTML = html;
}
function badgeClass(name) {
    var map = {'morning_papers':'badge-morning_papers','site_monitor':'badge-site_monitor','daily_report':'badge-daily_report','github_agent_trend':'badge-github_agent_trend'};
    if (name.startsWith('research/')) return 'badge-research';
    return map[name] || 'badge-default';
}
function escHtml(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
async function generateDescriptions(btn) {
    btn.disabled = true;
    btn.textContent = 'Generating...';
    var resultEl = document.getElementById('gen-result');
    resultEl.textContent = '';
    try {
        var resp = await fetch('/api/generate-descriptions', {method: 'POST'});
        var data = await resp.json();
        if (data.error) {
            resultEl.textContent = 'Error: ' + data.error;
            btn.disabled = false;
            btn.textContent = 'Generate Descriptions';
            return;
        }
        resultEl.textContent = 'Generating descriptions in background...';
        var pollId = setInterval(async function() {
            try {
                var r = await fetch('/api/rag/status');
                var d = await r.json();
                var total = d.total_docs || 0;
                var desc = d.docs_with_description || 0;
                resultEl.textContent = 'Progress: ' + desc + '/' + total + ' descriptions';
                if (!d.generating) {
                    clearInterval(pollId);
                    resultEl.textContent = 'Done: ' + desc + ' descriptions generated';
                    btn.remove();
                }
            } catch(e) {}
        }, 3000);
    } catch(e) {
        resultEl.textContent = 'Failed: ' + e.message;
        btn.disabled = false;
        btn.textContent = 'Generate Descriptions';
    }
}
async function advanceResearch(slug, btn) {
    btn.disabled = true;
    var orig = btn.textContent;
    btn.textContent = 'Running...';
    btn.classList.add('running');
    try {
        var resp = await fetch('/api/research/' + slug + '/advance', {method: 'POST'});
        var data = await resp.json();
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Research session completed. Refreshing...');
            location.reload();
        }
    } catch(e) {
        alert('Request failed: ' + e.message);
    }
    btn.disabled = false;
    btn.textContent = orig;
    btn.classList.remove('running');
}
async function submitResearch(e) {
    e.preventDefault();
    var topic = document.getElementById('research-topic').value.trim();
    if (!topic) return;
    var resultEl = document.getElementById('create-result');
    var btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Creating...';
    try {
        var resp = await fetch('/api/research/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic: topic})
        });
        var data = await resp.json();
        if (data.error) {
            resultEl.textContent = 'Error: ' + data.error;
            btn.disabled = false;
            btn.textContent = 'Create Project';
        } else {
            window.location.href = '/research/' + data.slug;
        }
    } catch(e) {
        resultEl.textContent = 'Failed: ' + e.message;
        btn.disabled = false;
        btn.textContent = 'Create Project';
    }
}
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


def _esc(text: str) -> str:
    """HTML-escape text for safe rendering"""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _task_icon(task_name: str) -> tuple[str, str]:
    if task_name.startswith("research/"):
        return ("R", "#ec4899")
    return _TASK_ICONS.get(task_name, (task_name[0].upper(), "#6b7280"))


def _badge_class(task_name: str) -> str:
    if task_name.startswith("research/"):
        return "badge-research"
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
    active_nav: str = "",
) -> str:
    date_counts = date_counts or {}
    items = []
    for d in dates:
        cls = ' class="active"' if d == active_date else ""
        cnt = date_counts.get(d, 0)
        count_html = f'<span class="count">{cnt}</span>' if cnt else ""
        items.append(f'<li><a href="/date/{d}"{cls}>{d}{count_html}</a></li>')
    date_list = "\n".join(items) if items else "<li>No dates</li>"

    nav_items = [
        ("research", "Research", "/research"),
        ("tasks", "Task Manager", "/tasks"),
        ("compare", "Compare", "/compare"),
        ("bookmarks", "Bookmarks", "/bookmarks"),
        ("ask", "Semantic Search", "/ask"),
    ]
    nav_links = []
    for key, label, href in nav_items:
        cls = ' class="active"' if key == active_nav else ""
        nav_links.append(f'<li><a href="{href}"{cls}>{label}</a></li>')
    nav_html = "\n".join(nav_links)

    return f"""
<div class="sidebar">
    <div class="sidebar-brand">
        <h1>Report Viewer</h1>
        <p>Auto Research Reports</p>
    </div>
    <div class="sidebar-section">
        <div class="sidebar-section-title">Navigation</div>
        <ul>{nav_html}</ul>
    </div>
    <div class="sidebar-section">
        <div class="sidebar-section-title">Dates</div>
        <ul>{date_list}</ul>
    </div>
    <div class="sidebar-footer">
        <button class="theme-btn" onclick="toggleTheme()" style="width:100%">Toggle Theme</button>
    </div>
</div>"""


def _render_card(
    r: dict, bookmarked: bool = False, show_bookmark: bool = False
) -> str:
    letter, color = _task_icon(r["task_name"])
    badge_cls = _badge_class(r["task_name"])
    star_cls = "active" if bookmarked else ""
    star_char = "\u2605" if bookmarked else "\u2606"
    bookmark_html = ""
    if show_bookmark:
        rdate = r["date"]
        rfile = r["filename"]
        bookmark_html = (
            f'<button class="bookmark-star {star_cls}" '
            f"onclick=\"toggleBookmark('{rdate}', '{rfile}', this)\">"
            f"{star_char}</button>"
        )
    # Display label: research/slug -> "Research: slug"
    display_name = r["task_name"]
    badge_label = r["task_name"]
    if r["task_name"].startswith("research/"):
        slug = r["task_name"][len("research/"):]
        display_name = f"Research: {slug}"
        badge_label = "research"
    return f"""<a href="/report/{r['date']}/{r['filename']}" style="text-decoration:none;color:inherit">
<div class="card">
    <div class="card-row">
        <div class="card-icon" style="background:{color}">{letter}</div>
        <div class="card-body">
            <div class="card-title"><a href="/report/{r['date']}/{r['filename']}">{display_name}</a></div>
            <div class="card-meta">
                <span class="badge {badge_cls}">{badge_label}</span>
                &nbsp;&middot;&nbsp; {r['display_time']} &middot; {r['date']}
            </div>
        </div>
        <div class="card-actions">
            {bookmark_html}
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
    bookmarked: bool = False,
) -> str:
    """Render a single report with markdown content"""
    star_cls = "active" if bookmarked else ""
    star_char = "\u2605" if bookmarked else "\u2606"
    body = f"""
<div class="layout">
{_sidebar(dates, active_date=date, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>{title}</h1>
    </div>
    <div class="action-bar">
        <a href="/date/{date}" class="back-link">&larr; {date}</a>
        <a href="/api/reports/{date}/{filename}/download" class="action-btn">Download .md</a>
        <button class="bookmark-star {star_cls}" onclick="toggleBookmark('{date}', '{filename}', this)">{star_char}</button>
    </div>
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


def render_task_list(
    dates: list[str],
    tasks: list[dict],
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the task list page"""
    task_cards = []
    for t in tasks:
        enabled_cls = "badge-enabled" if t["enabled"] else "badge-disabled"
        enabled_text = "Enabled" if t["enabled"] else "Disabled"

        last_run = ""
        if t.get("last_log"):
            log = t["last_log"]
            status_cls = "badge-success" if log.success else "badge-failed"
            status_text = "Success" if log.success else "Failed"
            cost = log.cost or "-"
            duration = log.duration or "-"
            last_run = (
                f'<span class="badge {status_cls}">{status_text}</span> '
                f'&middot; {log.timestamp[:19]} &middot; {cost} &middot; {duration}'
            )
        else:
            last_run = '<span style="color:var(--muted)">No runs yet</span>'

        toggle_text = "Disable" if t["enabled"] else "Enable"
        task_cards.append(f"""
<div class="card">
    <div class="card-row">
        <div class="card-body">
            <div class="card-title"><a href="/tasks/{t['name']}">{t['name']}</a></div>
            <div class="card-meta">
                <span class="badge {enabled_cls}">{enabled_text}</span>
                &nbsp;&middot;&nbsp; skill: {t['skill']} &middot; {t.get('description', '')}
            </div>
            <div class="card-meta" style="margin-top:6px">{last_run}</div>
        </div>
        <div class="card-actions">
            <button class="run-btn" onclick="runTask('{t['name']}', this)">Run</button>
            <button class="toggle-btn" onclick="toggleTask('{t['name']}', this)">{toggle_text}</button>
        </div>
    </div>
</div>""")
    cards_html = "\n".join(task_cards) if task_cards else '<div class="empty-state"><p>No tasks configured</p></div>'

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="tasks", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Task Manager</h1></div>
    {cards_html}
</div>
</div>"""
    return _page("Task Manager", body)


def render_task_detail(
    dates: list[str],
    task_name: str,
    task_config: dict,
    history: list,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render task detail page with config and execution history"""
    # Config section
    skill = task_config.get("skill", "")
    description = task_config.get("description", "")
    enabled = task_config.get("enabled", True)
    max_turns = task_config.get("max_turns", 10)
    params = task_config.get("parameters", {})
    import json
    params_str = json.dumps(params, ensure_ascii=False, indent=2) if params else "-"

    enabled_cls = "badge-enabled" if enabled else "badge-disabled"
    enabled_text = "Enabled" if enabled else "Disabled"
    toggle_text = "Disable" if enabled else "Enable"

    # History table
    history_rows = ""
    for h in history:
        status_cls = "badge-success" if h.success else "badge-failed"
        status_text = "OK" if h.success else "FAIL"
        cost = h.cost or "-"
        duration = h.duration or "-"
        turns = str(h.turns) if h.turns else "-"
        ts = h.timestamp[:19] if h.timestamp else "-"
        # Derive report filename from log
        report_fn = h.filename.replace(".txt", "_report.md")
        report_link = f'<a href="/report/{h.date}/{report_fn}">Report</a>' if h.success else "-"
        log_link = f'<a href="/logs/{h.date}/{h.filename}">Log</a>'
        history_rows += f"""
<tr>
    <td>{h.date}</td>
    <td>{h.display_time}</td>
    <td><span class="badge {status_cls}">{status_text}</span></td>
    <td>{cost}</td>
    <td>{duration}</td>
    <td>{turns}</td>
    <td>{log_link}</td>
    <td>{report_link}</td>
</tr>"""

    history_section = ""
    if history_rows:
        history_section = f"""
<div class="log-section">
    <div class="log-section-title">Execution History</div>
    <table class="history-table">
        <tr><th>Date</th><th>Time</th><th>Status</th><th>Cost</th><th>Duration</th><th>Turns</th><th>Log</th><th>Report</th></tr>
        {history_rows}
    </table>
</div>"""
    else:
        history_section = '<div class="empty-state"><p>No execution history</p></div>'

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="tasks", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>{task_name}</h1></div>
    <div class="action-bar">
        <a href="/tasks" class="back-link">&larr; All Tasks</a>
        <button class="run-btn" onclick="runTask('{task_name}', this)">Run Now</button>
        <button class="toggle-btn" onclick="toggleTask('{task_name}')">{toggle_text}</button>
    </div>
    <div class="log-section">
        <div class="log-section-title">Configuration</div>
        <div class="config-grid">
            <span class="config-key">Skill</span><span class="config-val">{skill}</span>
            <span class="config-key">Description</span><span class="config-val">{description}</span>
            <span class="config-key">Status</span><span class="config-val"><span class="badge {enabled_cls}">{enabled_text}</span></span>
            <span class="config-key">Max Turns</span><span class="config-val">{max_turns}</span>
            <span class="config-key">Parameters</span><span class="config-val"><pre style="margin:0;padding:8px;font-size:12px;background:var(--bg);border-radius:4px">{params_str}</pre></span>
        </div>
    </div>
    {history_section}
</div>
</div>"""
    return _page(f"Task - {task_name}", body)


def render_log(
    dates: list[str],
    log_entry,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render a structured log entry"""
    status_cls = "badge-success" if log_entry.success else "badge-failed"
    status_text = "Success" if log_entry.success else "Failed"
    cost = log_entry.cost or "-"
    duration = log_entry.duration or "-"
    turns = str(log_entry.turns) if log_entry.turns else "-"
    ts = log_entry.timestamp[:19] if log_entry.timestamp else "-"

    result_section = ""
    if log_entry.result:
        if log_entry.success:
            result_section = f"""
<div class="log-section">
    <div class="log-section-title">Result</div>
    <div class="report-content" style="padding:16px">{log_entry.result}</div>
</div>"""
        else:
            result_section = f"""
<div class="log-section">
    <div class="log-section-title">Error</div>
    <pre>{log_entry.result}</pre>
</div>"""

    body = f"""
<div class="layout">
{_sidebar(dates, date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>Log: {log_entry.task_name}</h1>
    </div>
    <div class="action-bar">
        <a href="/tasks/{log_entry.task_name}" class="back-link">&larr; Task Detail</a>
    </div>
    <div class="log-header">
        <div class="log-stat"><div class="label">Task</div><div class="value" style="font-size:14px">{log_entry.task_name}</div></div>
        <div class="log-stat"><div class="label">Skill</div><div class="value" style="font-size:14px">{log_entry.skill}</div></div>
        <div class="log-stat"><div class="label">Time</div><div class="value" style="font-size:14px">{ts}</div></div>
        <div class="log-stat"><div class="label">Status</div><div class="value"><span class="badge {status_cls}">{status_text}</span></div></div>
        <div class="log-stat"><div class="label">Cost</div><div class="value">{cost}</div></div>
        <div class="log-stat"><div class="label">Duration</div><div class="value">{duration}</div></div>
        <div class="log-stat"><div class="label">Turns</div><div class="value">{turns}</div></div>
    </div>
    <div class="log-section">
        <div class="log-section-title">Prompt</div>
        <pre>{log_entry.prompt}</pre>
    </div>
    {result_section}
</div>
</div>"""
    return _page(f"Log - {log_entry.task_name}", body)


def render_compare(
    dates: list[str],
    task_types: list[str],
    current_task: str = "",
    left_date: str = "",
    left_file: str = "",
    right_date: str = "",
    right_file: str = "",
    left_html: str = "",
    right_html: str = "",
    diff_html: str = "",
    left_dates: list[str] | None = None,
    left_files: list[dict] | None = None,
    right_dates: list[str] | None = None,
    right_files: list[dict] | None = None,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the report comparison page"""
    import json as _json

    # Task type selector
    task_options = ['<option value="">Select task type</option>']
    for t in task_types:
        sel = ' selected' if t == current_task else ""
        task_options.append(f'<option value="{t}"{sel}>{t}</option>')

    # Date selectors
    def _date_opts(items: list[str], current: str) -> str:
        opts = ['<option value="">Select date</option>']
        for d in items:
            sel = ' selected' if d == current else ""
            opts.append(f'<option value="{d}"{sel}>{d}</option>')
        return "".join(opts)

    def _file_opts(items: list[dict], current: str) -> str:
        opts = ['<option value="">Select report</option>']
        for f in items or []:
            sel = ' selected' if f["filename"] == current else ""
            opts.append(f'<option value="{f["filename"]}"{sel}>{f["display_time"]}</option>')
        return "".join(opts)

    left_date_opts = _date_opts(left_dates or dates, left_date)
    left_file_opts = _file_opts(left_files, left_file)
    right_date_opts = _date_opts(right_dates or dates, right_date)
    right_file_opts = _file_opts(right_files, right_file)

    compare_result = ""
    if diff_html:
        compare_result = f'<div class="compare-container">{diff_html}</div>'

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="compare", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Compare Reports</h1></div>
    <form method="get" action="/compare" class="log-section">
        <div class="log-section-title">Select Reports</div>
        <div style="margin-bottom:12px">
            <label style="font-size:13px;font-weight:600;color:var(--muted)">Task Type</label>
            <select name="task_type" onchange="this.form.submit()" style="width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:6px;font-size:13px;background:var(--surface);color:var(--text)">
                {"".join(task_options)}
            </select>
        </div>
        <div class="compare-form">
            <div class="compare-col">
                <h3>Left (Older)</h3>
                <select name="left_date">{left_date_opts}</select>
                <select name="left_file">{left_file_opts}</select>
            </div>
            <div class="compare-col">
                <h3>Right (Newer)</h3>
                <select name="right_date">{right_date_opts}</select>
                <select name="right_file">{right_file_opts}</select>
            </div>
        </div>
        <button type="submit" class="run-btn">Compare</button>
    </form>
    {compare_result}
</div>
</div>"""
    return _page("Compare Reports", body)


def render_bookmarks(
    dates: list[str],
    bookmarks: list[dict],
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the bookmarks page"""
    cards = []
    for b in bookmarks:
        cards.append(_render_card(b, bookmarked=True, show_bookmark=True))
    cards_html = "\n".join(cards) if cards else '<div class="empty-state"><p>No bookmarks yet</p></div>'

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="bookmarks", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Bookmarks</h1></div>
    {cards_html}
</div>
</div>"""
    return _page("Bookmarks", body)


def render_ask(
    dates: list[str],
    query: str = "",
    results: list | None = None,
    error: str = "",
    rag_available: bool = False,
    rag_status: dict | None = None,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the semantic search (Ask) page"""
    results = results or []
    rag_status = rag_status or {}

    # Status indicator
    dot_cls = "active" if rag_available else "inactive"
    total = rag_status.get("total_docs", 0)
    with_desc = rag_status.get("docs_with_description", 0)
    desc_text = (
        f", {with_desc}/{total} with descriptions"
        if total > 0
        else ""
    )
    gen_btn = (
        f'<button class="ask-submit" style="margin-left:8px;padding:4px 12px;font-size:12px" '
        f'onclick="generateDescriptions(this)">Generate Descriptions</button>'
        if rag_available and with_desc < total
        else ""
    )
    status_html = (
        f'<div class="ask-status">'
        f'<span class="ask-status-dot {dot_cls}"></span>'
        f'{"Indexed {0} reports{1}".format(total, desc_text) if rag_available else "RAG unavailable"}'
        f'{gen_btn}'
        f'<span id="gen-result" style="margin-left:8px;font-size:12px"></span>'
        f"</div>"
    )

    error_html = f'<div class="ask-error">{error}</div>' if error else ""

    # Pre-rendered server-side results (for GET /ask?q=...)
    results_html = ""
    if results:
        cards = []
        for r in results:
            pct = int(r.relevance * 100)
            sections_html = ""
            for s in r.sections:
                sections_html += (
                    f'<div class="ask-snippet">'
                    f'<div class="ask-snippet-title">{_esc(s["title"])}</div>'
                    f'{_esc(s["snippet"])}'
                    f"</div>"
                )
            reasoning_html = (
                f'<div class="ask-reasoning">{_esc(r.reasoning)}</div>'
                if r.reasoning
                else ""
            )
            badge_cls = _badge_class(r.task_name)
            rel_cls = "relevance-high" if pct >= 70 else "relevance-med" if pct >= 40 else "relevance-low"
            cards.append(
                f"""<div class="ask-result-card">
    <div class="ask-result-header">
        <div class="ask-result-title"><a href="/report/{r.date}/{r.filename}">{_esc(r.task_name)} &mdash; {r.display_time}</a></div>
        <span class="relevance-badge {rel_cls}">{pct}% match</span>
    </div>
    <div class="card-meta"><span class="badge {badge_cls}">{_esc(r.task_name)}</span> &middot; {r.date}</div>
    {reasoning_html}
    <div class="ask-snippets">{sections_html}</div>
</div>"""
            )
        results_html = "\n".join(cards)
    elif query and not error:
        results_html = '<div class="empty-state"><p>No relevant reports found</p></div>'

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="ask", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Semantic Search</h1></div>
    {status_html}
    {error_html}
    <div class="ask-container">
        <div class="ask-input-wrap">
            <textarea id="ask-input" placeholder="Ask a question about your reports... (Ctrl+Enter to search)">{_esc(query)}</textarea>
            <button class="ask-submit" onclick="askQuery(this)">Search</button>
        </div>
        <div id="ask-results">{results_html}</div>
    </div>
</div>
</div>"""
    return _page("Semantic Search", body)


# ── Research Project Templates ──────────────────────────────────────────

_PHASE_ORDER = ["discovery", "analysis", "solution_draft", "validation", "finalization", "complete"]
_PHASE_LABELS = {
    "discovery": "1. Discovery",
    "analysis": "2. Analysis",
    "solution_draft": "3. Solution Draft",
    "validation": "4. Validation",
    "finalization": "5. Finalization",
    "complete": "Done",
}
_PHASE_COLORS = {
    "discovery": "#3b82f6",
    "analysis": "#8b5cf6",
    "solution_draft": "#f59e0b",
    "validation": "#10b981",
    "finalization": "#6366f1",
    "complete": "#10b981",
}


def _phase_progress_bar(current_phase: str) -> str:
    """Render a horizontal phase progress bar"""
    current_idx = _PHASE_ORDER.index(current_phase) if current_phase in _PHASE_ORDER else 0
    steps = []
    for i, phase in enumerate(_PHASE_ORDER):
        color = _PHASE_COLORS.get(phase, "#6b7280")
        if i < current_idx:
            css_class = "phase-step-done"
        elif i == current_idx:
            css_class = "phase-step-active"
        else:
            css_class = "phase-step-pending"
        label = _PHASE_LABELS.get(phase, phase)
        steps.append(
            f'<div class="phase-step {css_class}" style="--phase-color:{color}">'
            f'<div class="phase-dot"></div>'
            f'<div class="phase-label">{label}</div>'
            f"</div>"
        )
    return f'<div class="phase-progress">{"".join(steps)}</div>'


def render_research_list(
    dates: list[str],
    projects: list,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the research project list page"""
    if not projects:
        cards_html = """<div class="empty-state">
            <p>No research projects yet</p>
            <a href="/research/new" class="action-btn" style="margin-top:12px">Create New Project</a>
        </div>"""
    else:
        cards = []
        for p in projects:
            phase_color = _PHASE_COLORS.get(p.phase, "#6b7280")
            phase_label = _PHASE_LABELS.get(p.phase, p.phase)
            confidence = p.confidence
            cards.append(f"""
<div class="card" onclick="location.href='/research/{p.slug}'" style="cursor:pointer">
    <div class="card-row">
        <div class="card-icon" style="background:{phase_color}">{p.phase[0].upper()}</div>
        <div class="card-body">
            <div class="card-title">{_esc(p.topic)}</div>
            <div class="card-meta">
                <span class="badge" style="background:{phase_color}20;color:{phase_color}">{phase_label}</span>
                &middot; Confidence: {confidence}%
                &middot; Sessions: {p.total_sessions}
                &middot; Sources: {p.source_count}
            </div>
        </div>
    </div>
</div>""")
        cards_html = "\n".join(cards)

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>Research Projects</h1>
        <a href="/research/new" class="run-btn" style="text-decoration:none">New Project</a>
    </div>
    {cards_html}
</div>
</div>"""
    return _page("Research", body)


def render_research_detail(
    dates: list[str],
    project,
    state_content: str,
    sessions: list,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render research project detail page"""
    phase_bar = _phase_progress_bar(project.phase)
    phase_color = _PHASE_COLORS.get(project.phase, "#6b7280")

    # Session list
    session_items = ""
    for s in sessions[:10]:
        session_items += f'<li><a href="/research/{project.slug}/sessions/{s.filename}">{s.timestamp}</a></li>'
    session_list = f"<ul>{session_items}</ul>" if session_items else '<span style="color:var(--muted)">No sessions yet</span>'

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>{_esc(project.topic)}</h1>
    </div>
    <div class="action-bar">
        <a href="/research" class="back-link">&larr; All Projects</a>
        <a href="/research/{project.slug}/solution" class="action-btn">Solution</a>
        <a href="/research/{project.slug}/checklist" class="action-btn">Checklist</a>
        <a href="/research/{project.slug}/todo" class="action-btn">TODO</a>
        <a href="/research/{project.slug}/sessions" class="action-btn">Sessions</a>
        <button class="run-btn" onclick="advanceResearch('{project.slug}', this)">Advance Research</button>
    </div>
    <div class="log-section">
        <div class="log-section-title">Progress</div>
        {phase_bar}
    </div>
    <div class="log-header">
        <div class="log-stat"><div class="label">Phase</div><div class="value"><span class="badge" style="background:{phase_color}20;color:{phase_color}">{_esc(project.phase)}</span></div></div>
        <div class="log-stat"><div class="label">Confidence</div><div class="value">{project.confidence}%</div></div>
        <div class="log-stat"><div class="label">Sessions</div><div class="value">{project.total_sessions}</div></div>
        <div class="log-stat"><div class="label">TODO</div><div class="value">{project.todo_completed}/{project.todo_completed + project.todo_pending}</div></div>
        <div class="log-stat"><div class="label">Last Updated</div><div class="value" style="font-size:13px">{_esc(project.last_updated or '-')}</div></div>
    </div>
    <div class="log-section">
        <div class="log-section-title">Next Action</div>
        <p>{_esc(project.next_action or 'Not specified')}</p>
    </div>
    <div class="log-section">
        <div class="log-section-title">Recent Sessions</div>
        {session_list}
    </div>
</div>
</div>"""
    return _page(f"Research - {project.topic}", body)


def render_research_solution(
    dates: list[str],
    slug: str,
    topic: str,
    html_content: str,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the solution document"""
    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Solution: {_esc(topic)}</h1></div>
    <div class="action-bar">
        <a href="/research/{slug}" class="back-link">&larr; Project</a>
        <a href="/research/{slug}/checklist" class="action-btn">Checklist</a>
    </div>
    <div class="report-content">{html_content}</div>
</div>
</div>"""
    return _page(f"Solution - {topic}", body)


def render_research_checklist(
    dates: list[str],
    slug: str,
    topic: str,
    html_content: str,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the verification checklist"""
    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Checklist: {_esc(topic)}</h1></div>
    <div class="action-bar">
        <a href="/research/{slug}" class="back-link">&larr; Project</a>
        <a href="/research/{slug}/solution" class="action-btn">Solution</a>
    </div>
    <div class="report-content">{html_content}</div>
</div>
</div>"""
    return _page(f"Checklist - {topic}", body)


def render_research_todo(
    dates: list[str],
    slug: str,
    topic: str,
    html_content: str,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the research TODO page"""
    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Research TODO: {_esc(topic)}</h1></div>
    <div class="action-bar">
        <a href="/research/{slug}" class="back-link">&larr; Project</a>
        <a href="/research/{slug}/solution" class="action-btn">Solution</a>
        <a href="/research/{slug}/checklist" class="action-btn">Checklist</a>
    </div>
    <div class="report-content">{html_content}</div>
</div>
</div>"""
    return _page(f"TODO - {topic}", body)


def render_research_sessions(
    dates: list[str],
    slug: str,
    topic: str,
    sessions: list,
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the session list page"""
    if not sessions:
        session_html = '<div class="empty-state"><p>No sessions yet</p></div>'
    else:
        rows = ""
        for s in sessions:
            rows += f"""
<tr>
    <td><a href="/research/{slug}/sessions/{s.filename}">{_esc(s.timestamp)}</a></td>
    <td>{s.filename}</td>
</tr>"""
        session_html = f"""
<table class="history-table">
    <tr><th>Timestamp</th><th>File</th></tr>
    {rows}
</table>"""

    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header"><h1>Sessions: {_esc(topic)}</h1></div>
    <div class="action-bar">
        <a href="/research/{slug}" class="back-link">&larr; Project</a>
    </div>
    <div class="log-section">
        <div class="log-section-title">Session History</div>
        {session_html}
    </div>
</div>
</div>"""
    return _page(f"Sessions - {topic}", body)


def render_research_new(
    dates: list[str],
    date_counts: dict[str, int] | None = None,
) -> str:
    """Render the new research project form"""
    body = f"""
<div class="layout">
{_sidebar(dates, active_nav="research", date_counts=date_counts)}
<div class="main">
    <div class="header">
        <h1>New Research Project</h1>
    </div>
    <div class="action-bar">
        <a href="/research" class="back-link">&larr; All Projects</a>
    </div>
    <div class="log-section">
        <div class="log-section-title">Create Project</div>
        <form id="new-research-form" onsubmit="submitResearch(event)" style="max-width:600px">
            <div style="margin-bottom:16px">
                <label style="display:block;font-size:13px;font-weight:600;color:var(--muted);margin-bottom:6px">Research Topic</label>
                <textarea id="research-topic" name="topic" rows="3" required
                    style="width:100%;padding:12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:var(--surface);color:var(--text);resize:vertical;font-family:inherit"
                    placeholder="Describe the research question or topic to investigate..."></textarea>
            </div>
            <div style="margin-bottom:16px">
                <label style="display:block;font-size:13px;font-weight:600;color:var(--muted);margin-bottom:6px">Depth Level</label>
                <select name="max_depth" style="width:200px;padding:8px 12px;border:1px solid var(--border);border-radius:8px;font-size:13px;background:var(--surface);color:var(--text)">
                    <option value="1">1 - Quick overview</option>
                    <option value="2">2 - Standard</option>
                    <option value="3" selected>3 - Thorough</option>
                    <option value="4">4 - Deep dive</option>
                    <option value="5">5 - Exhaustive</option>
                </select>
            </div>
            <button type="submit" class="run-btn" style="padding:10px 24px">Create Project</button>
            <span id="create-result" style="margin-left:12px;font-size:13px;color:var(--muted)"></span>
        </form>
    </div>
</div>
</div>"""
    return _page("New Research", body)
