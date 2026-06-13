"""MSS Action Recorder - Launch Playwright browser with HAR recording.

Opens a normal-looking Chromium browser that records all HTTP traffic to a HAR file.
Service managers operate the MSS platform as usual, and all API calls are captured.

Usage:
    python scripts/mss_record.py
    python scripts/mss_record.py --url https://mss.example.com
    python scripts/mss_record.py --output data/mss_captures/session.har

Prerequisites:
    pip install playwright && playwright install chromium
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="MSS Action Recorder (Playwright HAR)")
    parser.add_argument("--url", default="", help="MSS platform URL to open on start")
    parser.add_argument("--output-dir", default="data/mss_captures", help="Directory to save HAR files")
    parser.add_argument("--timeout", type=int, default=0, help="Recording timeout in minutes (0 = unlimited)")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed.", file=sys.stderr)
        print("  pip install playwright", file=sys.stderr)
        print("  playwright install chromium", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate session-based filename
    now = datetime.now(timezone.utc)
    har_path = output_dir / f"session_{now.strftime('%Y%m%d_%H%M%S')}.har"

    print("=" * 60)
    print("  MSS Action Recorder")
    print("=" * 60)
    print(f"  HAR output: {har_path}")
    print(f"  URL:        {args.url or '(navigate manually)'}")
    print()
    print("  Instructions:")
    print("  1. Operate the MSS platform as usual")
    print("  2. All API calls are being recorded")
    print("  3. Close the browser when done to save the recording")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",  # Less detectable
            ],
        )

        context = browser.new_context(
            record_har_path=str(har_path),
            record_har_content="embed",  # Include response bodies
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )

        page = context.new_page()

        if args.url:
            page.goto(args.url)

        # Wait for the user to close the browser manually
        try:
            print("Recording... (close the browser window when done)")
            page.wait_for_event("close", timeout=args.timeout * 60000 if args.timeout else 0)
        except Exception:
            pass  # Timeout or user closed

        # Ensure HAR is flushed
        context.close()
        browser.close()

    print(f"\nRecording saved: {har_path}")
    print(f"File size: {har_path.stat().st_size / 1024:.1f} KB")

    # Verify HAR file has content
    import json
    try:
        with open(har_path, encoding="utf-8") as f:
            har = json.load(f)
        entries = har.get("log", {}).get("entries", [])
        api_entries = [
            e for e in entries
            if not _is_static(e.get("request", {}).get("url", ""))
        ]
        print(f"Total requests: {len(entries)}, API requests: {len(api_entries)}")
    except Exception as e:
        print(f"Warning: could not parse HAR: {e}")


def _is_static(url: str) -> bool:
    """Check if a URL is a static resource."""
    static_exts = {
        ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".ico",
        ".svg", ".woff", ".woff2", ".ttf", ".eot", ".map",
    }
    path = url.split("?")[0].split("#")[0].lower()
    return any(path.endswith(ext) for ext in static_exts)


if __name__ == "__main__":
    main()
