"""
SOP Verifier — 对比期望 SOP 步骤 vs 实际采集的 A11y 事件

读取执行后的最新 pageSessionId 采集数据，与期望 SOP 模板对比，
输出验证报告（匹配/缺失/多余/顺序偏差）。

用法:
  python sop_verifier.py sop_templates.yaml --page-session <pageSessionId>
  python sop_verifier.py sop_templates.yaml  # 自动取最新
"""
import subprocess
import json
import sys
import time
import yaml
from collections import defaultdict


def fetch_actual_events(page_session_id=""):
    """从 Umami 读取实际采集的 A11y 事件"""

    if not page_session_id:
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
        page_session_id = result.stdout.strip()
        if not page_session_id:
            return [], ""

    sid = page_session_id.replace("'", "''").replace(";", "")

    sql = (
        "SELECT row_to_json(t) FROM ("
        "  SELECT"
        "    MAX(CASE WHEN ed.data_key = 'eventType' THEN ed.string_value END) as eventtype,"
        "    MAX(CASE WHEN ed.data_key = 'role' THEN ed.string_value END) as role,"
        "    MAX(CASE WHEN ed.data_key = 'name' THEN ed.string_value END) as name,"
        "    MAX(CASE WHEN ed.data_key = 'inputValue' THEN ed.string_value END) as inputvalue,"
        "    MAX(CASE WHEN ed.data_key = 'selectedText' THEN ed.string_value END) as selectedtext,"
        "    MAX(CASE WHEN ed.data_key = 'context.role' THEN ed.string_value END) as contextrole,"
        "    MAX(CASE WHEN ed.data_key = 'context.label' THEN ed.string_value END) as contextlabel"
        "  FROM website_event we"
        "  JOIN event_data ed ON we.event_id = ed.website_event_id"
        "  WHERE we.event_name = 'a11y-action'"
        "  AND we.event_id IN (SELECT website_event_id FROM event_data "
        "  WHERE data_key = 'pageSessionId' AND string_value = '" + sid + "')"
        "  GROUP BY we.event_id, we.created_at"
        "  ORDER BY we.created_at ASC"
        "  LIMIT 200"
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

    return events, page_session_id


def normalize_events(events):
    """归一化事件：过滤噪音、提取关键信息"""
    normalized = []
    for ev in events:
        et = (ev.get("eventtype") or "").lower()
        role = (ev.get("role") or "").lower()
        name = (ev.get("name") or "").strip()
        ctx = (ev.get("contextlabel") or ev.get("contextrole") or "").strip()

        # 跳过非操作事件
        if role in ("tabpanel", "generic", "main", "navigation"):
            continue
        if name in ("null", "None", ""):
            continue
        if et == "change":
            continue  # change 由 fill/select 自动触发

        # 映射为统一的操作签名
        if et == "click" and role == "checkbox":
            sig = f"toggle:{name}"
        elif et == "input" and role == "listbox":
            val = ev.get("selectedtext") or ""
            sig = f"select:{name}:{val}"
        elif et == "input":
            val = ev.get("inputvalue") or ""
            sig = f"fill:{name}:{val}"
        elif et == "click":
            sig = f"click:{role}:{name}"
        else:
            sig = f"{et}:{role}:{name}"

        normalized.append({
            "signature": sig,
            "action": et,
            "role": role,
            "name": name,
            "context": ctx,
            "value": ev.get("inputvalue") or ev.get("selectedtext") or "",
        })

    return normalized


def normalize_expected(sop_steps):
    """将期望 SOP 步骤归一化为操作签名"""
    expected = []
    for step in sop_steps:
        action = step.get("action", "")
        role = (step.get("role") or "").lower()
        name = (step.get("name") or "").strip()
        param = step.get("param")
        recorded = step.get("recorded_value", "")

        # 跳过非操作步骤
        if role in ("tabpanel", "generic", "main", "navigation"):
            continue
        if name in ("null", "None", ""):
            continue

        # 构建操作签名（参数化：用 {param} 占位符代替具体值）
        if action == "click" and role == "checkbox":
            sig = f"toggle:{name}"
        elif action in ("input", "change") and role == "listbox":
            sig = f"select:{name}:*"  # * = any value
        elif action == "input":
            sig = f"fill:{name}:*"  # * = any value
        elif action == "click":
            sig = f"click:{role}:{name}"
        else:
            sig = f"{action}:{role}:{name}"

        expected.append({
            "signature": sig,
            "action": action,
            "role": role,
            "name": name,
            "param": param,
        })

    return expected


def match_steps(expected, actual):
    """对比期望步骤 vs 实际采集，返回验证结果（宽松匹配）"""
    results = []
    used_actual = set()

    for exp in expected:
        exp_sig = exp["signature"]
        matched = False
        match_detail = ""

        for i, act in enumerate(actual):
            if i in used_actual:
                continue
            act_sig = act["signature"]

            # 精确匹配
            if act_sig == exp_sig:
                matched = True
                match_detail = f"exact match at pos {i}"
                used_actual.add(i)
                break

            # 模糊匹配（通配符 * 匹配任意值）
            exp_parts = exp_sig.split(":")
            act_parts = act_sig.split(":")
            if len(exp_parts) == len(act_parts):
                fuzzy_match = True
                for ep, ap in zip(exp_parts, act_parts):
                    if ep != "*" and ep != ap:
                        fuzzy_match = False
                        break
                if fuzzy_match:
                    matched = True
                    match_detail = f"fuzzy match at pos {i} (actual: {act_sig})"
                    used_actual.add(i)
                    break

            # 宽松匹配：click:textbox:X 匹配 fill:X:* （agent-browser fill 不产生 click）
            if exp_sig.startswith("click:textbox:") and act_sig.startswith("fill:"):
                exp_name = exp_sig.split(":", 2)[2]
                act_name = act_sig.split(":", 2)[1] if len(act_sig.split(":")) > 2 else ""
                if exp_name and act_name and exp_name in act_name:
                    matched = True
                    match_detail = f"loose match (click->fill) at pos {i}"
                    used_actual.add(i)
                    break

        results.append({
            "expected": exp_sig,
            "matched": matched,
            "detail": match_detail or "NOT FOUND",
        })

    extra_steps = []
    for i, act in enumerate(actual):
        if i not in used_actual:
            extra_steps.append(act["signature"])

    return results, extra_steps[:5]


def verify_sop(sop, actual_events):
    """验证单个 SOP — 按 context 过滤实际事件后匹配"""
    expected = normalize_expected(sop["steps"])

    # 按 context 过滤实际事件
    sop_context = (sop.get("context") or "").strip().lower()
    if sop_context:
        filtered_actual = [ev for ev in actual_events
                          if sop_context in (ev.get("context") or "").lower()
                          or (ev.get("context") or "").lower() in sop_context]
    else:
        filtered_actual = actual_events

    results, extra = match_steps(expected, filtered_actual)

    matched_count = sum(1 for r in results if r["matched"])
    total = len(results)

    status = "PASS" if matched_count == total else ("PARTIAL" if matched_count > 0 else "FAIL")

    return {
        "sop_name": sop["name"],
        "context": sop["context"],
        "status": status,
        "matched": matched_count,
        "total": total,
        "actual_in_context": len(filtered_actual),
        "steps": results,
        "extra_actual": extra,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SOP Verifier")
    parser.add_argument("yaml_file", help="Expected SOP YAML template")
    parser.add_argument("--page-session", default="", help="pageSessionId to verify against")
    args = parser.parse_args()

    print("=== SOP Verifier ===\n")

    # Load expected SOPs
    with open(args.yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    expected_sops = data.get("sops", [])

    # Fetch actual events
    actual_events, session_id = fetch_actual_events(args.page_session)
    if not actual_events:
        print("No actual events found.")
        sys.exit(1)

    actual_normalized = normalize_events(actual_events)

    print(f"PageSession: {session_id[:8]}...")
    print(f"Actual events: {len(actual_events)} raw, {len(actual_normalized)} normalized")
    print(f"Expected SOPs: {len(expected_sops)}\n")

    # Verify each SOP
    all_results = []
    for sop in expected_sops:
        result = verify_sop(sop, actual_normalized)
        all_results.append(result)

        print(f"--- {result['sop_name']} ({result['context']}) ---")
        print(f"  Status: {result['status']} ({result['matched']}/{result['total']})")
        for step in result["steps"]:
            mark = "[OK]" if step["matched"] else "[MISS]"
            print(f"    {mark} {step['expected']}")
        if result["extra_actual"]:
            print(f"  Extra actual steps: {result['extra_actual']}")
        print()

    # Summary
    total_pass = sum(1 for r in all_results if r["status"] == "PASS")
    print("=" * 50)
    print(f"VERIFICATION SUMMARY: {total_pass}/{len(all_results)} SOPs passed")

    # Save report
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "page_session": session_id,
        "total_sops": len(all_results),
        "passed": total_pass,
        "results": all_results,
    }
    report_path = "sop_verification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
