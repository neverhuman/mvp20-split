"""Test-only admission barriers in real independent owner processes."""

import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.compiler import SchemaCatalog, ToolCatalog
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.successors.transfer import CarryTransfer
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import create_engine, text


def wait(path):
    deadline = time.monotonic() + 45
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("successor_probe_barrier_timeout")
        time.sleep(0.01)


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_bytes())
    who = job["principal"]
    principal = RuntimePrincipal(who["actor_id"], Scope.model_validate(who["scope"]), frozenset(who["actions"]))
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(job["definition"])), ToolCatalog([]), SchemaCatalog([]))
    command = parse_graph_command("graph.admit_successor", json.dumps(job["command"]))
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"], connect_args={"options": "-c statement_timeout=15000"})
    original = CarryTransfer.persist

    def persist(transfer, conn, params, run_id):
        original(transfer, conn, params, run_id)
        path.with_suffix(".before_commit").write_text(run_id, encoding="utf-8")
        if job.get("hold_before_commit"):
            wait(path.with_suffix(".commit_release"))

    CarryTransfer.persist = persist
    try:
        with engine.connect() as conn:
            backend = conn.execute(text("SELECT pg_backend_pid()")).scalar_one()
        path.with_suffix(".ready").write_text(json.dumps({"process": os.getpid(), "backend": backend}), encoding="utf-8")
        wait(Path(job["start"]))
        receipt = GraphAdmission(engine, PlanCatalog([entry])).admit_successor(principal, command)
        path.with_suffix(".committed").write_text(receipt.model_dump_json(), encoding="utf-8")
        if job.get("hold_after_commit"):
            wait(path.with_suffix(".reply_release"))
        path.with_suffix(".reply").write_text(receipt.model_dump_json(), encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
