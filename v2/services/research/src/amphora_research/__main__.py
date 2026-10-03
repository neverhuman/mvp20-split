"""Explicit local Research identity server; no import-time connections."""

import argparse
import json
from pathlib import Path

import uvicorn
from sqlalchemy.exc import SQLAlchemyError

from .transport.host import ResearchHost


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve", "check"])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8084)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between1024 and65535")
    try:
        with args.config.open("rb") as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError("configuration_limit")
        config = json.loads(raw.decode("utf-8"))
        host = ResearchHost.configured(config)
    except (OSError, ValueError, SQLAlchemyError):
        print(json.dumps({"status": "configuration_or_owner_unavailable"}))
        return 2
    try:
        if args.command == "check":
            print(json.dumps({"status": "ready", "authority": host.app.state.authority}))
            return 0
        uvicorn.run(host.app, host="127.0.0.1", port=args.port, limit_concurrency=16)
    finally:
        host.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
