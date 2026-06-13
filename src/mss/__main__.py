"""CLI entry point for MSS SOP execution.

Usage:
    python -m src.mss execute --sop handle_alert --params '{"alert_id": "ALT-123"}'
    python -m src.mss list-sops
    python -m src.mss validate --sop handle_alert
    python -m src.mss resume --execution-id 2026-06-01/handle_alert_143022 --decision approve
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.mss.executor import SopExecutor

DEFAULT_EXECUTIONS_DIR = Path("data/mss_executions")


def main() -> None:
    parser = argparse.ArgumentParser(description="MSS SOP Execution Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-sops
    subparsers.add_parser("list-sops", help="List available SOP definitions")

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate a SOP definition")
    validate_parser.add_argument("--sop", required=True, help="SOP name to validate")

    # execute
    exec_parser = subparsers.add_parser("execute", help="Execute a SOP")
    exec_parser.add_argument("--sop", required=True, help="SOP name to execute")
    exec_parser.add_argument("--params", default="{}", help="Input parameters as JSON string")

    # resume (for approval workflows)
    resume_parser = subparsers.add_parser("resume", help="Resume a paused SOP execution")
    resume_parser.add_argument("--execution-id", required=True, help="Execution ID (date/filename)")
    resume_parser.add_argument("--decision", required=True, choices=["approve", "reject"], help="Approval decision")
    resume_parser.add_argument("--approver", default="cli_user", help="Approver identifier")
    resume_parser.add_argument("--justification", default="", help="Justification for the decision")

    # list-executions
    list_exec_parser = subparsers.add_parser("list-executions", help="List execution records")
    list_exec_parser.add_argument("--status", default="", help="Filter by status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    executor = SopExecutor()

    if args.command == "list-sops":
        sops = executor.list_sops()
        if not sops:
            print("No SOP definitions found.")
            return
        for sop in sops:
            print(f"  {sop['name']}: {sop['description']} ({sop['file']})")

    elif args.command == "validate":
        try:
            sop = executor.load_sop(args.sop)
            missing = executor.validate_inputs(sop, {})
            print(f"SOP '{args.sop}' is valid.")
            print(f"  Steps: {len(sop.get('steps', []))}")
            if missing:
                print(f"  Required params: {', '.join(missing)}")
            else:
                print("  No required parameters.")
        except Exception as e:
            print(f"Validation failed: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "execute":
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON params: {e}", file=sys.stderr)
            sys.exit(1)

        result = asyncio.run(executor.run(args.sop, params))
        _print_result(result)

        if result.status in ("failed",):
            sys.exit(1)

    elif args.command == "resume":
        _handle_resume(args, executor)

    elif args.command == "list-executions":
        _handle_list_executions(args)


def _print_result(result) -> None:
    """Print execution result as JSON."""
    print(json.dumps({
        "sop_name": result.sop_name,
        "status": result.status,
        "output": result.output,
        "error": result.error,
        "steps": [
            {
                "step_id": s.step_id,
                "step_name": s.step_name,
                "status": s.status,
                "http_status": s.http_status,
                "step_type": s.step_type,
                "extracted": s.extracted,
                "error": s.error,
                "duration_ms": s.duration_ms,
                "retry_count": s.retry_count,
                "approver": s.approver,
                "notification_sent": s.notification_sent,
            }
            for s in result.steps
        ],
    }, ensure_ascii=False, indent=2))


def _handle_resume(args, executor: SopExecutor) -> None:
    """Resume a paused execution with an approval decision."""
    # Parse execution ID: "2026-06-01/handle_alert_143022"
    parts = args.execution_id.split("/")
    if len(parts) == 2:
        date, filename = parts
    else:
        print(f"Invalid execution ID format. Use: YYYY-MM-DD/filename", file=sys.stderr)
        sys.exit(1)

    filepath = DEFAULT_EXECUTIONS_DIR / date / f"{filename}.json" if not filename.endswith(".json") else DEFAULT_EXECUTIONS_DIR / date / filename

    if not filepath.exists():
        print(f"Execution record not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    with open(filepath, encoding="utf-8") as f:
        execution = json.load(f)

    if execution.get("status") != "awaiting_approval":
        print(f"Execution is not awaiting approval (status: {execution.get('status')})", file=sys.stderr)
        sys.exit(1)

    # Update the approval step in the execution record
    for step in execution.get("steps", []):
        if step.get("status") == "awaiting_approval":
            step["status"] = args.decision + "d"  # "approved" or "rejected"
            step["approver"] = args.approver
            step["decision_time"] = _now_iso()
            step["justification"] = args.justification
            break

    execution["status"] = "approved" if args.decision == "approve" else "rejected"
    execution["finished_at"] = _now_iso()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(execution, f, ensure_ascii=False, indent=2)

    print(f"Execution {args.execution_id} {args.decision}d by {args.approver}")
    print(json.dumps(execution, ensure_ascii=False, indent=2))


def _handle_list_executions(args) -> None:
    """List execution records."""
    if not DEFAULT_EXECUTIONS_DIR.exists():
        print("No execution records found.")
        return

    for date_dir in sorted(DEFAULT_EXECUTIONS_DIR.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for filepath in sorted(date_dir.glob("*.json"), reverse=True):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                status = data.get("status", "")
                if args.status and status != args.status:
                    continue
                sop = data.get("sop_name", "")
                started = data.get("started_at", "")
                step_count = len(data.get("steps", []))
                print(f"  {date_dir.name}/{filepath.stem}  {sop}  {status}  {step_count} steps  {started}")
            except Exception:
                pass


def _now_iso() -> str:
    """Return current UTC time as ISO format string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
