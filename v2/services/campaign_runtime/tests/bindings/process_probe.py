"""Actual owner-process barriers; Artifact behavior is explicitly scripted."""

import json
import os
import sys
import time
from pathlib import Path

from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.compiler import (
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
)
from amphora_campaign_runtime.coordinator import PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import Scope
from amphora_contracts_runtime import parse_command
from sqlalchemy import create_engine, text
from support import MemoryArtifacts


def wait(path):
    deadline = time.monotonic() + 45
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("binding_probe_barrier_timeout")
        time.sleep(0.01)


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_bytes())
    who = job["principal"]
    principal = RuntimePrincipal(who["actor_id"], Scope.model_validate(who["scope"]), frozenset(who["actions"]))
    schemas = SchemaCatalog([PinnedSchema(SchemaIdentity(**item["identity"]), item["body"].encode()) for item in job["schemas"]])
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(job["definition"])), ToolCatalog([]), schemas)
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"], connect_args={"options": "-c statement_timeout=15000"})

    class Peer(MemoryArtifacts):
        def reserve(self, reservation):
            path.with_suffix(".reserving").write_text("prepared", encoding="utf-8")
            if job.get("hold_reserve"):
                wait(path.with_suffix(".reserve_release"))
            return super().reserve(reservation)

    class Coordinator(BindingCoordinator):
        def commit(self, conn, work, outputs, resources):
            path.with_suffix(".before_commit").write_text("prepared", encoding="utf-8")
            if job.get("hold_before_commit"):
                wait(path.with_suffix(".commit_release"))
            return super().commit(conn, work, outputs, resources)

    peer = Peer(principal.scope)
    peer.documents = {key: body.encode() for key, body in job["documents"].items()}
    try:
        with engine.connect() as conn:
            backend = conn.execute(text("SELECT pg_backend_pid()")).scalar_one()
        path.with_suffix(".ready").write_text(json.dumps({"process": os.getpid(), "backend": backend}), encoding="utf-8")
        wait(Path(job["start"]))
        if "cancel" in job:
            reply = AuthorityCommands(engine).cancel(principal, parse_command("runtime.cancel", json.dumps(job["cancel"])))
            changed = reply.outcome.status == "accepted"
        else:
            changed = Coordinator(engine, PlanCatalog([entry]), peer, peer).tick(principal)
        path.with_suffix(".committed").write_text("returned", encoding="utf-8")
        if job.get("hold_after_commit"):
            wait(path.with_suffix(".reply_release"))
        path.with_suffix(".reply").write_text(json.dumps({"changed": changed}), encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
