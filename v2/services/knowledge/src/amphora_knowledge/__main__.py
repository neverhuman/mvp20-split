"""Explicit local Knowledge server, with separate operator-owned migration."""

import argparse
import json
from pathlib import Path

import uvicorn
from sqlalchemy.exc import SQLAlchemyError

from .transport.host import KnowledgeHost
from .validation.transport import strict_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve", "check"])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8085)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    try:
        with args.config.open("rb") as stream:
            raw = stream.read(524289)
        if len(raw) > 524288:
            raise ValueError("configuration_limit")
        host = KnowledgeHost.configured(strict_json(raw))
    except (OSError, ValueError, SQLAlchemyError):
        print(json.dumps({"status": "configuration_or_owner_unavailable"}))
        return 2
    try:
        if args.command == "check":
            print(json.dumps({"status": "ready", "authority": "structural_only"}))
            return 0
        uvicorn.run(host.app, host="127.0.0.1", port=args.port, limit_concurrency=16, access_log=False)
    finally:
        host.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
