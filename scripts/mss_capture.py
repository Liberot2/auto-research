"""CLI wrapper for starting MSS action capture via mitmproxy.

Usage:
    python scripts/mss_capture.py --port 8080 --mss-domain mss.example.com
    python scripts/mss_capture.py --port 8080 --mss-domain mss.example.com --output-dir data/captures
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="MSS Action Capture via mitmproxy")
    parser.add_argument("--port", type=int, default=8080, help="Proxy listen port (default: 8080)")
    parser.add_argument("--mss-domain", required=True, help="MSS platform domain to capture")
    parser.add_argument("--output-dir", default="data/mss_captures", help="Capture output directory")
    args = parser.parse_args()

    addon_path = Path(__file__).parent.parent / "addons" / "mitmproxy_mss_capture.py"
    if not addon_path.exists():
        print(f"Error: addon not found at {addon_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "mitmproxy",
        "--listen-port", str(args.port),
        "--set", f"mss_domain={args.mss_domain}",
        "--set", f"output_dir={output_dir}",
        "-s", str(addon_path),
    ]

    print(f"Starting MSS capture proxy on port {args.port}")
    print(f"  MSS domain: {args.mss_domain}")
    print(f"  Output dir: {output_dir}")
    print(f"  Configure browser proxy: 127.0.0.1:{args.port}")
    print()

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nCapture stopped.")
    except FileNotFoundError:
        print("Error: mitmproxy not installed. Run: pip install mitmproxy", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
