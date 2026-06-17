"""
SOP Executor — 读取 YAML SOP 模板 + 参数，通过 agent-browser 执行

用法:
  python sop_executor.py sop_templates.yaml --params '{"keyword":"hello","format":"CSV File"}'
  python sop_executor.py sop_templates.yaml --sop "导出报告" --params '{"format":"PDF Document"}'
"""
import subprocess
import json
import sys
import time
import yaml
import re


def run_ab(cmd):
    """执行 agent-browser 命令，返回 (success, output)"""
    full_cmd = f"agent-browser {cmd}"
    result = subprocess.run(
        full_cmd, shell=True, capture_output=True, timeout=30,
        encoding="utf-8", errors="replace"
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    success = result.returncode == 0 and "\u2717" not in stdout
    output = stdout.strip()
    if success:
        print(f"  PASS: {cmd[:80]}")
    else:
        print(f"  FAIL: {cmd[:80]}")
        if stderr:
            print(f"    Error: {stderr.strip()[:100].encode('ascii', 'replace').decode()}")
    return success, output


def get_refs():
    """获取当前页面的交互元素 ref 映射"""
    success, output = run_ab("snapshot -i")
    if not success:
        return {}

    refs = {}
    # 解析 snapshot 输出的行，提取 role + name → ref
    # 格式示例: '  - textbox "Search reports" [ref=e12]'
    pattern = re.compile(r'- (\w+)(?:\s+"([^"]*)")?.*\[ref=(\w+)\]')

    for line in output.split("\n"):
        match = pattern.search(line)
        if match:
            role = match.group(1).lower()
            name = (match.group(2) or "").strip()
            ref = match.group(3)
            key = f"{role}:{name}" if name else f"{role}:{ref}"
            refs[key] = ref
            # 同时用 role only 作为 fallback
            if role not in refs:
                refs[role] = ref

    return refs


def find_ref(refs, role, name):
    """从 refs 中查找元素，先精确匹配再模糊匹配"""
    role = role.lower()
    name = (name or "").strip()

    # 1. 精确匹配 role:name
    key = f"{role}:{name}"
    if key in refs:
        return refs[key]

    # 2. 忽略前导/尾随空格
    for k, v in refs.items():
        if k.startswith(role + ":") and k.split(":", 1)[1].strip() == name:
            return v

    # 3. 模糊匹配（name 包含关系）
    for k, v in refs.items():
        if k.startswith(role + ":"):
            ref_name = k.split(":", 1)[1]
            if name in ref_name or ref_name in name:
                return v

    # 4. role only
    if role in refs:
        return refs[role]

    return None


def execute_step(step, params, refs):
    """执行单个 SOP 步骤，返回 (success, detail)"""
    action = step.get("action", "")
    role = step.get("role", "")
    name = step.get("name", "").strip() if step.get("name") else ""
    param = step.get("param")
    recorded = step.get("recorded_value", "")

    # 确定值：优先参数，其次录制值
    value = ""
    if param and params and param in params:
        value = str(params[param])
    elif recorded:
        value = str(recorded)

    # 查找元素 ref
    ref = find_ref(refs, role, name)

    # 跳过噪音步骤
    if role in ("tabpanel", "generic", "main", "navigation"):
        return True, "skipped (non-actionable)"
    if name == "null" or name == "None":
        return True, "skipped (null name)"

    if action == "click":
        if role == "checkbox":
            # checkbox toggle
            if ref:
                success, _ = run_ab(f"click @{ref}")
                return success, f"toggle checkbox @{ref}"
            return False, "checkbox not found"
        elif ref:
            success, _ = run_ab(f"click @{ref}")
            return success, f"click @{ref}"
        else:
            success, _ = run_ab(f'find role {role} click --name "{name}"')
            return success, f"semantic click {role}:{name}"

    elif action in ("input", "change", "fill"):
        if role == "listbox":
            # select dropdown
            if ref:
                success, _ = run_ab(f'select @{ref} "{value}"')
                return success, f"select @{ref} = {value}"
            else:
                success, _ = run_ab(f'find role {role} select --name "{name}" "{value}"')
                return success, f"semantic select {value}"
        elif ref:
            success, _ = run_ab(f'fill @{ref} "{value}"')
            return success, f"fill @{ref} = {value}"
        else:
            success, _ = run_ab(f'find role {role} fill --name "{name}" "{value}"')
            return success, f"semantic fill {value}"

    elif action == "toggle":
        if ref:
            success, _ = run_ab(f"click @{ref}")
            return success, f"toggle @{ref}"

    return True, f"unknown action ({action})"


def execute_sop(sop, params, target_url):
    """执行完整 SOP"""
    name = sop["name"]
    steps = sop["steps"]
    print(f"\n{'='*50}")
    print(f"Executing SOP: {name}")
    print(f"Steps: {len(steps)} | Params: {json.dumps(params, ensure_ascii=False)}")
    print(f"{'='*50}\n")

    results = []

    for i, step in enumerate(steps):
        step_num = i + 1
        action_desc = f'{step["action"]} {step["role"]}'
        if step.get("name"):
            action_desc += f' "{step["name"]}"'

        # 每步前刷新 refs（页面可能变化）
        if step["role"] in ("tab", "button") and step["action"] == "click":
            time.sleep(1)
            refs = get_refs()
        elif i == 0:
            refs = get_refs()

        success, detail = execute_step(step, params, refs)
        results.append({
            "step": step_num,
            "action": action_desc,
            "success": success,
            "detail": detail,
        })

        if not success:
            print(f"  WARN: Step {step_num} failed, retrying...")
            time.sleep(1)
            refs = get_refs()
            success, detail = execute_step(step, params, refs)
            results[-1]["success"] = success
            results[-1]["detail"] = detail + " (retry)"

        time.sleep(0.5)

    # Summary
    passed = sum(1 for r in results if r["success"])
    print(f"\n--- Result: {passed}/{len(results)} steps passed ---\n")

    return results, passed, len(results)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SOP Executor via agent-browser")
    parser.add_argument("yaml_file", help="SOP YAML template file")
    parser.add_argument("--sop", default=None, help="SOP name to execute (default: first)")
    parser.add_argument("--params", default="{}", help="JSON parameters")
    parser.add_argument("--url", default="http://localhost:8080", help="Target URL")
    parser.add_argument("--all", action="store_true", help="Execute all SOPs in sequence")
    args = parser.parse_args()

    # Load YAML
    with open(args.yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sops = data.get("sops", [])
    params = json.loads(args.params)

    print(f"Loaded {len(sops)} SOPs from {args.yaml_file}")
    print(f"Target: {args.url}")
    print(f"Params: {json.dumps(params, ensure_ascii=False)}")

    # Open browser
    run_ab(f"open {args.url}")
    time.sleep(2)

    # Select SOP(s)
    if args.all:
        to_execute = sops
    elif args.sop:
        to_execute = [s for s in sops if s["name"] == args.sop]
        if not to_execute:
            print(f"SOP '{args.sop}' not found. Available: {[s['name'] for s in sops]}")
            sys.exit(1)
    else:
        to_execute = [sops[0]]  # first SOP

    # Execute
    all_results = []
    for sop in to_execute:
        results, passed, total = execute_sop(sop, params, args.url)
        all_results.append({
            "sop": sop["name"],
            "passed": passed,
            "total": total,
            "results": results,
        })

    # Final summary
    print("\n" + "=" * 50)
    print("FINAL SUMMARY")
    print("=" * 50)
    for r in all_results:
        status = "PASS" if r["passed"] == r["total"] else "PARTIAL"
        print(f"  {status}: {r['sop']} ({r['passed']}/{r['total']})")

    # Screenshot
    run_ab("screenshot")
    run_ab("close")

    # Save report
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "url": args.url,
        "params": params,
        "sops": all_results,
    }
    report_path = "sop_execution_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
