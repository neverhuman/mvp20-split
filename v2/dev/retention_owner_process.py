"""Installed owner qualification host; each process imports one implementation only."""

import json
import sys
from pathlib import Path

import uvicorn


def main():
    owner, config, port, ready = sys.argv[1:]
    if owner == "data":
        from amphora_data_artifacts.hosting import Host
    elif owner == "runtime":
        from amphora_campaign_runtime.hosting import Host
    else:
        raise ValueError("Explicit qualification owner required")
    host = Host.load(config)
    try:
        record = {"owner": owner, "installed": True}
        if owner == "runtime":
            from amphora_campaign_runtime.coordinator.configuration import load_graphs
            raw = json.loads(Path(config).read_bytes())
            entries = load_graphs(raw["graphs"], Path(config).parent)
            record["plan_sha256"] = entries[0][0].plan.sha256
            record["plans"] = {entry.plan.document.definition.campaign_id: entry.plan.sha256 for entry, _, _ in entries}
        Path(ready).write_text(json.dumps(record), encoding="utf-8")
        uvicorn.run(host.app(), host="127.0.0.1", port=int(port), access_log=False)
    finally:
        host.close()


if __name__ == "__main__":
    main()
