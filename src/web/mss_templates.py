"""HTML templates for MSS SOP management pages.

Uses the same CSS variables and layout patterns as the main templates.py.
"""

import html
import json
from typing import Any

from src.web.templates import _CSS, _JS, _page


def _status_badge(status: str) -> str:
    """Render a status badge with color coding."""
    colors = {
        "success": "var(--green)",
        "failed": "var(--red)",
        "partial": "var(--orange)",
        "skipped": "var(--muted)",
    }
    color = colors.get(status, "var(--blue)")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500;">{html.escape(status)}</span>'


def render_captures_page(captures: list[dict[str, Any]]) -> str:
    """Render the captures list page."""
    rows = ""
    for c in captures:
        rows += f"""
        <div class="card" style="cursor:pointer" onclick="location.href='/mss/captures/{html.escape(c["filename"])}'">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <strong>{html.escape(c["session_id"])}</strong>
                    <span style="color:var(--muted);font-size:13px;margin-left:12px">{html.escape(c["mss_base_url"])}</span>
                </div>
                <span style="color:var(--muted);font-size:13px">{c["action_count"]} actions</span>
            </div>
            <div style="color:var(--text-secondary);font-size:13px;margin-top:6px">
                {html.escape(c["start_time"])} ~ {html.escape(c["end_time"])}
            </div>
        </div>"""

    content = f"""
    <div class="header">
        <h1>MSS Action Captures</h1>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:20px">
        Captured HTTP sessions from MSS platform via mitmproxy proxy.
        <a href="/mss/sops" style="margin-left:16px">View SOPs</a>
    </div>
    {rows if rows else '<div style="color:var(--muted)">No capture sessions found. Run <code>python scripts/mss_capture.py</code> to start capturing.</div>'}
    """

    return _page("MSS Captures", content, dates=[], active_nav="mss_captures")


def render_capture_detail(capture: dict[str, Any], filename: str) -> str:
    """Render a capture session detail page."""
    actions = capture.get("actions", [])
    rows = ""
    for a in actions:
        method_color = {
            "GET": "var(--blue)", "POST": "var(--green)",
            "PUT": "var(--orange)", "DELETE": "var(--red)",
            "PATCH": "var(--purple)",
        }.get(a.get("method", ""), "var(--muted)")

        status = a.get("response_status", "N/A")
        body_preview = ""
        if a.get("request_body"):
            body_str = json.dumps(a["request_body"], ensure_ascii=False)
            if len(body_str) > 200:
                body_str = body_str[:200] + "..."
            body_preview = f'<div style="font-size:12px;color:var(--text-secondary);margin-top:4px"><code>{html.escape(body_str)}</code></div>'

        rows += f"""
        <div class="card">
            <div style="display:flex;align-items:center;gap:10px">
                <span style="color:var(--muted);font-size:12px;min-width:24px">#{a.get("sequence", "")}</span>
                <span style="background:{method_color};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600">{html.escape(a.get("method", ""))}</span>
                <code style="font-size:13px;flex:1">{html.escape(a.get("path", ""))}</code>
                <span style="color:var(--muted);font-size:13px">{a.get("duration_ms", "N/A")}ms</span>
                {f'<span style="font-size:13px">{_status_badge(str(status) if status and 200 <= status < 300 else "failed")}</span>' if status else ""}
            </div>
            {body_preview}
        </div>"""

    content = f"""
    <div class="header">
        <h1>Capture: {html.escape(capture.get("session_id", filename))}</h1>
        <button class="theme-btn" onclick="generateSop()">Generate SOP</button>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:20px">
        {html.escape(capture.get("mss_base_url", ""))} &middot; {len(actions)} actions
        &middot; {html.escape(capture.get("start_time", ""))} ~ {html.escape(capture.get("end_time", ""))}
        &middot; <a href="/mss/captures">Back to list</a>
    </div>
    {rows if rows else '<div style="color:var(--muted)">No actions in this capture.</div>'}
    <script>
    function generateSop() {{
        fetch('/api/mss/captures/{html.escape(filename)}/generate-sop', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: '{{}}'}})
        .then(r => r.json())
        .then(d => alert(d.message + '\\n\\n' + d.hint))
        .catch(e => alert('Error: ' + e));
    }}
    </script>
    """

    return _page("Capture Detail", content, dates=[], active_nav="mss_captures")


def render_sops_page(sops: list[dict[str, Any]]) -> str:
    """Render the SOP list page."""
    rows = ""
    for s in sops:
        params_str = ", ".join(s.get("required_params", [])) or "None"
        rows += f"""
        <div class="card" style="cursor:pointer" onclick="location.href='/mss/sops/{html.escape(s["name"])}'">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <strong>{html.escape(s["name"])}</strong>
                    <span style="color:var(--muted);font-size:12px;margin-left:8px">v{html.escape(s.get("version", "1.0"))}</span>
                </div>
                <span style="color:var(--muted);font-size:13px">{s.get("step_count", 0)} steps</span>
            </div>
            <div style="color:var(--text-secondary);font-size:13px;margin-top:4px">
                {html.escape(s.get("description", ""))}
            </div>
            <div style="color:var(--muted);font-size:12px;margin-top:4px">
                Required params: {html.escape(params_str)} &middot; File: {html.escape(s.get("file", ""))}
            </div>
        </div>"""

    content = f"""
    <div class="header">
        <h1>MSS SOP Definitions</h1>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:20px">
        Standard Operating Procedures for MSS platform automation.
        <a href="/mss/captures" style="margin-left:16px">View Captures</a>
        <a href="/mss/executions" style="margin-left:16px">View Executions</a>
    </div>
    {rows if rows else '<div style="color:var(--muted)">No SOP definitions found. Add YAML files to <code>config/mss_sops/</code>.</div>'}
    """

    return _page("MSS SOPs", content, dates=[], active_nav="mss_sops")


def render_sop_detail(
    sop: dict[str, Any],
    name: str,
    executions: list[dict[str, Any]],
) -> str:
    """Render a SOP detail page with steps and execution form."""
    import yaml

    steps_html = ""
    for step in sop.get("steps", []):
        extract_str = ", ".join(f"{k} <- {v}" for k, v in step.get("extract", {}).items())
        condition_html = ""
        if step.get("condition"):
            condition_html = f'<div style="color:var(--orange);font-size:12px;margin-top:4px">Condition: <code>{html.escape(step["condition"])}</code></div>'

        steps_html += f"""
        <div class="card">
            <div style="display:flex;align-items:center;gap:10px">
                <span style="color:var(--muted);font-size:12px;min-width:60px">{html.escape(step.get("id", ""))}</span>
                <span style="background:var(--blue);color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600">{html.escape(step.get("method", "GET"))}</span>
                <code style="font-size:13px;flex:1">{html.escape(step.get("path", ""))}</code>
            </div>
            <div style="color:var(--text-secondary);font-size:13px;margin-top:4px">{html.escape(step.get("name", ""))}</div>
            {condition_html}
            {'<div style="font-size:12px;color:var(--green);margin-top:4px">Extract: ' + html.escape(extract_str) + '</div>' if extract_str else ''}
            {f'<div style="font-size:12px;color:var(--muted);margin-top:4px">Expect: status {step.get("expect", {}).get("status", "any")}</div>' if step.get("expect") else ''}
        </div>"""

    # Execution form
    input_params = sop.get("input_parameters", {})
    param_inputs = ""
    for pname, pschema in input_params.items():
        required = "required" if pschema.get("required") else ""
        default = pschema.get("default", "")
        desc = pschema.get("description", "")
        param_inputs += f"""
        <div style="margin-bottom:8px">
            <label style="font-size:13px;font-weight:500">{html.escape(pname)}
                {'<span style="color:var(--red)">*</span>' if pschema.get('required') else ''}
            </label>
            <input id="param-{html.escape(pname)}" placeholder="{html.escape(desc)}" value="{html.escape(str(default))}"
                {required} style="width:100%;padding:6px 10px;border:1px solid var(--border);border-radius:4px;margin-top:2px;font-size:13px">
        </div>"""

    # Execution history
    exec_rows = ""
    for e in executions:
        exec_rows += f"""
        <div class="card" style="cursor:pointer" onclick="location.href='/mss/executions/{e["date"]}/{e["filename"]}'">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span>{_status_badge(e.get("status", ""))}</span>
                <span style="color:var(--muted);font-size:13px">{html.escape(e.get("started_at", ""))}</span>
            </div>
        </div>"""

    content = f"""
    <div class="header">
        <h1>SOP: {html.escape(sop.get("name", name))}</h1>
        <a href="/mss/sops" class="theme-btn" style="text-decoration:none">Back to list</a>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:20px">
        {html.escape(sop.get("description", ""))} &middot; v{html.escape(sop.get("version", "1.0"))}
    </div>

    <h2 style="font-size:18px;margin-bottom:12px">Steps ({len(sop.get("steps", []))})</h2>
    {steps_html if steps_html else '<div style="color:var(--muted)">No steps defined.</div>'}

    <h2 style="font-size:18px;margin:24px 0 12px">Execute</h2>
    <div class="card">
        {param_inputs if param_inputs else '<div style="color:var(--muted)">No input parameters required.</div>'}
        <button class="theme-btn" onclick="executeSop()" style="margin-top:12px;background:var(--accent);color:#fff;border-color:var(--accent)">
            Execute SOP
        </button>
        <div id="exec-result" style="margin-top:12px;font-size:13px;display:none"></div>
    </div>

    {"<h2 style='font-size:18px;margin:24px 0 12px'>Execution History</h2>" + exec_rows if exec_rows else ""}

    <script>
    function executeSop() {{
        const params = {{}};
        {"".join(f'const v{pname} = document.getElementById("param-{pname}").value; if (v{pname}) params["{pname}"] = v{pname};'.replace(pname, pname.replace("-", "_")) for pname in input_params)}
        const resultDiv = document.getElementById("exec-result");
        resultDiv.style.display = "block";
        resultDiv.textContent = "Executing...";
        fetch('/api/mss/sops/{html.escape(name)}/execute', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(params)
        }})
        .then(r => r.json())
        .then(d => {{
            resultDiv.innerHTML = '<pre style="white-space:pre-wrap;font-size:12px">' + JSON.stringify(d, null, 2) + '</pre>';
        }})
        .catch(e => {{ resultDiv.textContent = 'Error: ' + e; }});
    }}
    </script>
    """

    return _page(f"SOP: {name}", content, dates=[], active_nav="mss_sops")


def render_executions_page(executions: list[dict[str, Any]]) -> str:
    """Render the executions list page."""
    rows = ""
    for e in executions:
        rows += f"""
        <div class="card" style="cursor:pointer" onclick="location.href='/mss/executions/{e["date"]}/{e["filename"]}'">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <strong>{html.escape(e.get("sop_name", ""))}</strong>
                    {_status_badge(e.get("status", ""))}
                </div>
                <span style="color:var(--muted);font-size:13px">{html.escape(e.get("started_at", ""))}</span>
            </div>
            <div style="color:var(--muted);font-size:12px;margin-top:4px">
                {e.get("step_count", 0)} steps &middot; {e.get("date", "")}
            </div>
        </div>"""

    content = f"""
    <div class="header">
        <h1>SOP Execution History</h1>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:20px">
        Past SOP executions with results.
        <a href="/mss/sops" style="margin-left:16px">View SOPs</a>
    </div>
    {rows if rows else '<div style="color:var(--muted)">No execution records found.</div>'}
    """

    return _page("MSS Executions", content, dates=[], active_nav="mss_executions")


def render_execution_detail(
    execution: dict[str, Any],
    date: str,
    filename: str,
) -> str:
    """Render an execution detail page."""
    steps_html = ""
    for s in execution.get("steps", []):
        steps_html += f"""
        <div class="card">
            <div style="display:flex;align-items:center;gap:10px">
                <span style="color:var(--muted);font-size:12px;min-width:80px">{html.escape(s.get("step_id", ""))}</span>
                {_status_badge(s.get("status", ""))}
                <span style="font-size:13px">{html.escape(s.get("step_name", ""))}</span>
                <span style="color:var(--muted);font-size:12px;margin-left:auto">{s.get("duration_ms", "N/A")}ms</span>
            </div>
            {f'<div style="font-size:12px;color:var(--muted);margin-top:4px">HTTP {s.get("http_status", "N/A")} {html.escape(s.get("method", ""))} {html.escape(s.get("path", ""))}</div>' if s.get("http_status") else ""}
            {f'<div style="font-size:12px;color:var(--green);margin-top:4px">Extracted: {html.escape(json.dumps(s.get("extracted", {}), ensure_ascii=False))}</div>' if s.get("extracted") else ""}
            {f'<div style="font-size:12px;color:var(--red);margin-top:4px">Error: {html.escape(s.get("error", ""))}</div>' if s.get("error") else ""}
        </div>"""

    output_html = ""
    if execution.get("output"):
        output_html = f"""
        <h2 style="font-size:18px;margin:24px 0 12px">Output</h2>
        <div class="card">
            <div style="font-size:14px">{html.escape(execution["output"].get("summary", ""))}</div>
            {f'<pre style="font-size:12px;margin-top:8px;white-space:pre-wrap">{html.escape(json.dumps(execution["output"].get("fields", {}), ensure_ascii=False, indent=2))}</pre>' if execution["output"].get("fields") else ""}
        </div>"""

    content = f"""
    <div class="header">
        <h1>Execution: {html.escape(execution.get("sop_name", ""))}</h1>
        <a href="/mss/executions" class="theme-btn" style="text-decoration:none">Back to list</a>
    </div>
    <div style="color:var(--text-secondary);margin-bottom:20px">
        {_status_badge(execution.get("status", ""))}
        &middot; {html.escape(execution.get("started_at", ""))} ~ {html.escape(execution.get("finished_at", ""))}
        &middot; <a href="/mss/sops/{html.escape(execution.get('sop_name', ''))}">View SOP</a>
    </div>
    {f'<div class="card" style="border-color:var(--red)"><div style="color:var(--red)">Error: {html.escape(execution.get("error", ""))}</div></div>' if execution.get("error") else ""}
    <h2 style="font-size:18px;margin-bottom:12px">Steps</h2>
    {steps_html if steps_html else '<div style="color:var(--muted)">No step details.</div>'}
    {output_html}
    """

    return _page("Execution Detail", content, dates=[], active_nav="mss_executions")
