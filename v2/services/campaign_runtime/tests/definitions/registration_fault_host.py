"""Owner-only test host: pause after durable registration, before definition writes.

Not packaged or reachable through production configuration. The acceptance controller
kills this owned process and restarts an ordinary independently installed host.
"""

import argparse
import json
import threading
from pathlib import Path

import uvicorn
from amphora_campaign_runtime.hosting import Host
from amphora_campaign_runtime.persistence.commands import CommandStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--marker", required=True, type=Path)
    args = parser.parse_args()
    original = CommandStore.register

    def register(store, command):
        record = original(store, command)
        if command.identity.actor_id == "studio_author" and command.identity.command_family == "definition.save":
            marker = args.marker.with_suffix(".tmp")
            marker.write_text(json.dumps({"operation_id": record.operation_id, "request_sha256": command.sha256,
                "identity": command.identity.model_dump(mode="json"), "status": record.status}), encoding="utf-8")
            marker.replace(args.marker)
            threading.Event().wait(45)
            raise TimeoutError("Registration fault host must be killed by controller")
        return record

    CommandStore.register = register
    host = Host.load(args.config)
    try:
        uvicorn.run(host.app(), host="127.0.0.1", port=args.port, access_log=False)
    finally:
        host.close()


if __name__ == "__main__":
    main()
