"""Test-only coordinator process barriers; absent from the installed Runtime package."""

import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.coordinator import GraphAdvancer
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import create_engine, text


def wait(path):
    deadline = time.monotonic() + 30
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("process_barrier_timeout")
        time.sleep(0.01)


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_text(encoding="utf-8"))
    raw = job["principal"]
    principal = RuntimePrincipal(raw["actor_id"], Scope.model_validate_json(json.dumps(raw["scope"])), frozenset(raw["actions"]))
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"], connect_args={"options": "-c statement_timeout=15000"})
    try:
        command = parse_graph_command("graph.advance", json.dumps(job["command"]))
        with engine.connect() as conn:
            backend = conn.execute(text("SELECT pg_backend_pid()")).scalar_one()
        path.with_suffix(".ready").write_text(json.dumps({"process": os.getpid(), "backend": backend}), encoding="utf-8")
        wait(Path(job["start"]))
        receipt = GraphAdvancer(engine).advance(principal, command)
        path.with_suffix(".committed").write_text("committed", encoding="utf-8")
        if job["hold_after_commit"]:
            wait(path.with_suffix(".release"))
        path.with_suffix(".reply").write_text(receipt.model_dump_json(), encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
