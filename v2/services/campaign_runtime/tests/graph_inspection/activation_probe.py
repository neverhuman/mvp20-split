"""Test-only barrier after real invocation INSERT, before the enclosing commit."""

import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.coordinator import GraphAdvancer
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import create_engine, event


def wait(path):
    deadline = time.monotonic() + 30
    while not path.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("activation_probe_barrier_timeout")
        time.sleep(0.01)


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_text(encoding="utf-8"))
    raw = job["principal"]
    principal = RuntimePrincipal(raw["actor_id"], Scope.model_validate_json(json.dumps(raw["scope"])), frozenset(raw["actions"]))
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"])

    @event.listens_for(engine, "after_cursor_execute")
    def inserted(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO runtime.activations"):
            path.with_suffix(".inserted").write_text("uncommitted", encoding="utf-8")
            wait(path.with_suffix(".release"))

    try:
        path.with_suffix(".ready").write_text("ready", encoding="utf-8")
        wait(Path(job["start"]))
        GraphAdvancer(engine).advance(principal, parse_graph_command("graph.advance", json.dumps(job["command"])))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
