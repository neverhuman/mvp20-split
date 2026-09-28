"""Independently hosted local registry; no startup migrations or tool execution."""

import argparse
import sys

import uvicorn

from .hosting import Host


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "check"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port invalid")
    try:
        host = Host.load(args.config)
    except Exception:
        print("Registry configuration or service-role readiness failed; no service started.", file=sys.stderr)
        return 2
    try:
        if args.action == "check":
            print("Registry configuration and service role ready")
        else:
            uvicorn.run(host.app(), host="127.0.0.1", port=args.port, access_log=False)
    finally:
        host.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
