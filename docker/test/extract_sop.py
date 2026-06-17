"""
SOP Extractor — 从 Umami event_data 自动提取参数化 SOP 模板

输入: pageSessionId (从 event_data 读取 TOON 事件序列)
输出: SOP 模板 (YAML格式, 可被 agent-browser 执行)

流程:
  1. 读取事件 → 2. 按 context 切分 → 3. 参数化 → 4. 输出 YAML
"""
import subprocess
import json
import sys
import yaml
from collections import defaultdict


def fetch_events(session_id=""):
    """从 Umami PostgreSQL 读取 A11y 事件"""

    if not session_id:
        # 取最新的 pageSessionId
        latest_sql = (
            "SELECT ed.string_value FROM event_data ed "
            "JOIN website_event we ON ed.website_event_id = we.event_id "
            "WHERE ed.data_key = 'pageSessionId' AND we.event_name = 'a11y-action' "
            "ORDER BY we.created_at DESC LIMIT 1;"
        )
        result = subprocess.run(
            ["docker", "exec", "umami-db", "psql", "-U", "umami", "-t", "-A", "-c", latest_sql],
            capture_output=True, text=True
        )
        session_id = result.stdout.strip()
        if not session_id:
            print("[]")
            sys.exit(0)

    session_id = session_id.replace("'", "''").replace(";", "")

    sql = (
        "SELECT row_to_json(t) FROM ("
        "  SELECT"
        "    MAX(CASE WHEN ed.data_key = 'eventType' THEN ed.string_value END) as eventtype,"
        "    MAX(CASE WHEN ed.data_key = 'role' THEN ed.string_value END) as role,"
        "    MAX(CASE WHEN ed.data_key = 'name' THEN ed.string_value END) as name,"
        "    MAX(CASE WHEN ed.data_key = 'toon' THEN ed.string_value END) as toon,"
        "    MAX(CASE WHEN ed.data_key = 'inputValue' THEN ed.string_value END) as inputvalue,"
        "    MAX(CASE WHEN ed.data_key = 'selectedText' THEN ed.string_value END) as selectedtext,"
        "    MAX(CASE WHEN ed.data_key = 'context.role' THEN ed.string_value END) as contextrole,"
        "    MAX(CASE WHEN ed.data_key = 'context.label' THEN ed.string_value END) as contextlabel,"
        "    MAX(CASE WHEN ed.data_key = 'timestamp' THEN ed.number_value END) as timestamp"
        "  FROM website_event we"
        "  JOIN event_data ed ON we.event_id = ed.website_event_id"
        "  WHERE we.event_name = 'a11y-action'"
        "  AND we.event_id IN (SELECT website_event_id FROM event_data "
        "  WHERE data_key = 'pageSessionId' AND string_value = '" + session_id + "')"
        "  GROUP BY we.event_id, we.created_at"
        "  ORDER BY we.created_at ASC"
        "  LIMIT 100"
        ") t;"
    )

    result = subprocess.run(
        ["docker", "exec", "umami-db", "psql", "-U", "umami", "-t", "-A", "-c", sql],
        capture_output=True, text=True
    )

    events = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    return events


def deduplicate(events):
    """去重: 300ms 内同 role+name+eventType 只保留一条; checkbox click+input 合并"""
    filtered = []
    last_sig = None
    last_ts = 0

    for ev in events:
        et = ev.get("eventtype", "")
        role = ev.get("role", "")
        name = ev.get("name", "")
        ts = int(ev.get("timestamp", 0) or 0)

        # 跳过 change（由 fill/selectOption 自动触发），但保留 listbox change（含选中值）
        if et == "change" and role != "listbox":
            continue

        # checkbox: click 后 500ms 内的 input 跳过（同一操作）
        if et == "input" and role == "checkbox":
            if last_sig == "click:checkbox:" + (name or "") and ts - last_ts < 500:
                continue

        sig = f"{et}:{role}:{name}"
        if sig == last_sig and ts - last_ts < 300:
            continue
        last_sig = sig
        last_ts = ts

        filtered.append(ev)

    return filtered


def segment_by_context(events):
    """按 context 切分操作片段"""
    segments = []
    current_segment = None
    current_ctx = None

    for ev in events:
        ctx_role = ev.get("contextrole", "")
        ctx_label = ev.get("contextlabel", "")
        ctx_key = f"{ctx_role}:{ctx_label}"

        if ctx_key != current_ctx:
            if current_segment:
                segments.append(current_segment)
            current_ctx = ctx_key
            current_segment = {
                "context_role": ctx_role,
                "context_label": ctx_label,
                "events": [],
            }
        if current_segment:
            current_segment["events"].append(ev)

    if current_segment:
        segments.append(current_segment)

    return segments


def extract_sop_from_segment(segment):
    """从操作片段提取参数化 SOP"""
    events = segment["events"]
    if not events:
        return None

    # 推断 SOP 名称
    ctx_label = segment.get("context_label", "")
    ctx_role = segment.get("context_role", "")

    # 步骤转换
    steps = []
    param_count = 0

    for ev in events:
        et = ev.get("eventtype", "")
        role = ev.get("role", "")
        name = ev.get("name", "")
        input_value = ev.get("inputvalue", "")
        selected_text = ev.get("selectedtext", "")

        step = {"action": et, "role": role}
        if name:
            step["name"] = name

        # 参数化逻辑
        if et == "input" and input_value:
            # 输入值 → 参数化
            param_count += 1
            param_name = infer_param_name(name, role)
            step["param"] = param_name
            step["recorded_value"] = input_value
        elif et == "input" and role == "listbox" and selected_text:
            # select 选项 → 参数化
            param_count += 1
            param_name = infer_param_name(name, role)
            step["param"] = param_name
            step["recorded_value"] = selected_text
        elif et == "click" and role == "checkbox":
            # checkbox → 固定动作（勾选/取消）
            step["action"] = "toggle"
        elif et == "click":
            # click → 固定步骤
            pass

        steps.append(step)

    sop = {
        "name": infer_sop_name(ctx_label, ctx_role, events),
        "context": ctx_label or ctx_role,
        "steps": steps,
        "param_count": param_count,
    }
    return sop


def infer_param_name(name, role):
    """从字段名推断参数名"""
    n = (name or "").lower()
    if "search" in n or "query" in n:
        return "keyword"
    if "name" in n:
        return "name"
    if "email" in n:
        return "email"
    if "phone" in n or "tel" in n:
        return "phone"
    if "password" in n:
        return "password"
    if "format" in n or "export" in n:
        return "format"
    return "value"


def infer_sop_name(ctx_label, ctx_role, events):
    """从上下文和事件推断 SOP 名称"""
    label = (ctx_label or "").lower()
    if "search" in label:
        return "搜索操作"
    if "export" in label:
        return "导出报告"
    if "setting" in label or "user setting" in label:
        return "修改设置"
    if "dialog" in label or "confirm" in label:
        return "确认操作"
    if "tablist" in (ctx_role or "").lower():
        return "导航切换"
    return f"操作流程 ({ctx_label or ctx_role})"


def to_agent_browser_command(step, params=None):
    """将 SOP 步骤转换为 agent-browser 命令"""
    action = step.get("action", "")
    role = step.get("role", "")
    name = step.get("name", "")
    param = step.get("param")
    recorded = step.get("recorded_value", "")

    # 参数值：优先用传入参数，否则用录制值
    value = ""
    if param and params and param in params:
        value = params[param]
    elif recorded:
        value = recorded

    # 构建 agent-browser 语义定位器
    name_flag = f' --name "{name}"' if name else ""

    if action == "click" and role == "checkbox":
        return f'agent-browser find role checkbox check --name "{name}"'
    elif action == "toggle":
        return f'agent-browser find role checkbox click --name "{name}"'
    elif action == "click":
        return f"agent-browser find role {role} click{name_flag}"
    elif action == "input" and role == "listbox":
        return f'agent-browser find role {role} select --name "{name}" "{value}"'
    elif action == "input":
        return f'agent-browser find role {role} fill{name_flag} "{value}"'
    elif action == "change":
        return f'agent-browser find role {role} select --name "{name}" "{value}"'
    return f"# Unknown: {action} {role} {name}"


def merge_duplicate_sops(sops):
    """合并相同名称的 SOP：保留最长版本，收集所有参数值变体"""
    by_name = defaultdict(list)
    for sop in sops:
        by_name[sop["name"]].append(sop)

    merged = []
    for name, group in by_name.items():
        # 选步骤最多的版本作为主模板
        best = max(group, key=lambda s: len(s["steps"]))

        # 收集所有参数值变体（用于展示可能的取值范围）
        param_values = defaultdict(set)
        for sop in group:
            for step in sop["steps"]:
                if step.get("param") and step.get("recorded_value"):
                    param_values[step["param"]].add(step["recorded_value"])

        # 附加参数取值范围
        params = {}
        for p, vals in param_values.items():
            params[p] = {"examples": sorted(vals), "count": len(group)}

        merged_sop = {
            "name": name,
            "context": best["context"],
            "steps": best["steps"],
            "param_count": best["param_count"],
            "occurrences": len(group),
            "param_values": params if params else {},
        }
        merged.append(merged_sop)

    return merged


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else ""

    print("=== SOP Extractor ===")
    print(f"Session: {session_id or '(latest)'}\n")

    # 1. Fetch events
    events = fetch_events(session_id)
    if not events:
        print("No events found.")
        return

    print(f"Raw events: {len(events)}")

    # 2. Deduplicate
    events = deduplicate(events)
    print(f"After dedup: {len(events)}")

    # 3. Segment by context
    segments = segment_by_context(events)
    print(f"Segments: {len(segments)}\n")

    # 4. Extract SOPs
    sops = []
    for seg in segments:
        sop = extract_sop_from_segment(seg)
        if sop and len(sop["steps"]) > 0:
            sops.append(sop)

    # 4.5 Merge duplicate SOPs
    sops = merge_duplicate_sops(sops)
    print(f"After merge: {len(sops)} unique SOPs\n")

    # 5. Output
    print("=" * 60)
    print("EXTRACTED SOPs")
    print("=" * 60)

    for i, sop in enumerate(sops):
        print(f"\n--- SOP {i+1}: {sop['name']} (x{sop['occurrences']}) ---")
        print(f"Context: {sop['context']}")
        print(f"Steps: {len(sop['steps'])} | Params: {sop['param_count']}")
        if sop.get("param_values"):
            for p, info in sop["param_values"].items():
                print(f"  param {p}: examples={info['examples']}")
        print()

        for j, step in enumerate(sop["steps"]):
            cmd = to_agent_browser_command(step)
            param_info = f" [param: {step['param']}={step.get('recorded_value', '')}]" if step.get("param") else ""
            print(f"  {j+1}. {cmd}{param_info}")

    # 6. Export YAML
    yaml_output = {
        "sops": [
            {
                "name": sop["name"],
                "context": sop["context"],
                "steps": sop["steps"],
            }
            for sop in sops
        ]
    }

    yaml_path = "sop_templates.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"\nYAML exported: {yaml_path}")

    # 7. Summary
    total_params = sum(s["param_count"] for s in sops)
    total_steps = sum(len(s["steps"]) for s in sops)
    print(f"\nSummary: {len(sops)} SOPs, {total_steps} steps, {total_params} parameters")


if __name__ == "__main__":
    main()
