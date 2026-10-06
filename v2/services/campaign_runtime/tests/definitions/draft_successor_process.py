"""Test-only process barriers after both records and after admission commit."""

import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog
from amphora_campaign_runtime.definitions.admission import DraftAdmissionGuard
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_contracts_core import Scope
from amphora_contracts_draft_successor import parse_draft_successor
from sqlalchemy import create_engine, text


def wait(path):
    deadline = time.monotonic() + 45
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("draft_successor_barrier_timeout")
        time.sleep(0.01)


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_bytes())
    who = job["principal"]
    principal = RuntimePrincipal(who["actor_id"], Scope.model_validate(who["scope"]), frozenset(who["actions"]))
    command = parse_draft_successor(json.dumps(job["command"]))
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"], connect_args={"options": "-c statement_timeout=15000"})
    universe = ValidationUniverse(principal.scope, (), ())
    guard = DraftAdmissionGuard(engine, {(principal.scope.tenant_id, principal.scope.project_id): universe})
    original = guard.record

    def record(*args):
        original(*args)
        path.with_suffix(".before_commit").write_text("both_records_written", encoding="utf-8")
        if job["boundary"] == "before_commit":
            wait(path.with_suffix(".release"))

    guard.record = record
    try:
        with engine.connect() as conn:
            backend = conn.execute(text("SELECT pg_backend_pid()")).scalar_one()
        path.with_suffix(".ready").write_text(json.dumps({"backend": backend}), encoding="utf-8")
        wait(Path(job["start"]))
        receipt = GraphAdmission(engine, PlanCatalog([]), bindings_enabled=True, drafts=guard).admit_draft_successor(principal, command)
        path.with_suffix(".committed").write_text(receipt.model_dump_json(), encoding="utf-8")
        if job["boundary"] == "after_commit":
            wait(path.with_suffix(".release"))
        path.with_suffix(".reply").write_text(receipt.model_dump_json(), encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
