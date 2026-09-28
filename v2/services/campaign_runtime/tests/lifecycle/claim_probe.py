"""Independent worker-domain probe; credentials/URL arrive only over stdin."""

import json
import sys

from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_core import Scope
from amphora_contracts_runtime import parse_command
from sqlalchemy import create_engine

if __name__ == "__main__":
    config = json.loads(sys.stdin.readline())
    engine = create_engine(config["url"], connect_args={"application_name": config["application"]})
    try:
        principal = RuntimePrincipal(config["actor"], Scope.model_validate(config["scope"]), frozenset({"claim"}))
        print("ready", flush=True)
        sys.stdin.readline()
        result = RuntimeLeases(engine).claim(principal, parse_command("runtime.claim", config["command"]))
        print(result.model_dump_json(), flush=True)
    finally:
        engine.dispose()
