"""Owner-process probe with explicit barriers; scripted Artifact peer, not peer acceptance."""

import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.coordinator import GraphAdvancer
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.waits.coordinator import WaitCoordinator
from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from amphora_contracts_runtime import parse_command
from sqlalchemy import create_engine, text


def wait(path):
    until = time.monotonic() + 30
    while not path.exists():
        if time.monotonic() >= until:
            raise TimeoutError("wait_process_barrier_timeout")
        time.sleep(0.01)


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_bytes())
    raw = job["principal"]
    principal = RuntimePrincipal(raw["actor_id"], Scope.model_validate(raw["scope"]), frozenset(raw["actions"]))
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"], connect_args={"options": "-c statement_timeout=15000"})

    class BarrierPeer:
        owner = "runtime"

        def reserve(self, reservation):
            path.with_suffix(".reserving").write_text("prepared", encoding="utf-8")
            if job.get("hold_reserve"):
                wait(path.with_suffix(".reserve_release"))
            return ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
                "reservation_id": "r-" + reservation.intent.intent_id,
                "artifact": reservation.artifact, "intent": reservation.intent}}})

    try:
        family = job["command"]["identity"]["command_family"]
        parser = parse_graph_command if family.startswith("graph.") else parse_command
        command = parser(family, json.dumps(job["command"]))
        with engine.connect() as conn:
            backend = conn.execute(text("SELECT pg_backend_pid()")).scalar_one()
        path.with_suffix(".ready").write_text(json.dumps({"process": os.getpid(), "backend": backend}), encoding="utf-8")
        wait(Path(job["start"]))
        if family == "graph.submit_receipt":
            receipt = WaitCoordinator(engine, BarrierPeer()).submit(principal, command)
        elif family == "graph.advance":
            receipt = GraphAdvancer(engine).advance(principal, command)
        else:
            assert family == "runtime.cancel"
            receipt = AuthorityCommands(engine).cancel(principal, command)
        path.with_suffix(".committed").write_text("committed", encoding="utf-8")
        if job.get("hold_after_commit"):
            wait(path.with_suffix(".release"))
        path.with_suffix(".reply").write_text(receipt.model_dump_json(), encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
