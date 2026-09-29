"""Source graph controller in a real process; explicitly scripted Artifact peer."""

import json
import os
import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

from amphora_campaign_runtime.coordinator import PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import parse_graph_command
from amphora_contracts_runtime import parse_command
from sqlalchemy import create_engine

# This probe is a test-process tier, not an independently installed SDK/owner proof.
sys.path.insert(0, str(Path(__file__).absolute().parents[4]))
from services.campaign_runtime.tests.baseline.catalog import catalog
from services.campaign_runtime.tests.baseline.execution import execute
from services.campaign_runtime.tests.bindings.support import MemoryArtifacts


def main():
    path = Path(sys.argv[1])
    job = json.loads(path.read_bytes())
    who = job["principal"]
    principal = RuntimePrincipal(who["actor_id"], Scope.model_validate(who["scope"]), frozenset(who["actions"]))
    releases, tools, schemas = catalog()
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(job["definition"])), tools, schemas)
    engine = create_engine(os.environ["GRAPH_PROBE_RUNTIME_URL"], connect_args={"options": "-c statement_timeout=15000"})
    peer = MemoryArtifacts(principal.scope)
    peer.documents = {key: value.encode() for key, value in job["documents"].items()}

    def command(family, payload):
        parser = parse_graph_command if family.startswith("graph.") else parse_command
        return parser(family, json.dumps({"identity": {"scope": who["scope"], "actor_id": principal.actor_id,
            "command_family": family, "command_id": uuid.uuid4().hex}, "payload": payload}))

    def snapshot(trace, states):
        return {"trace": trace, "states": states, "documents": {key: body.decode() for key, body in peer.documents.items()}}

    def after_stage(stage, trace, states):
        if job.get("interrupt") and stage == "score" and trace[-1]["input"]["candidate"]["generation"] == 1:
            path.with_suffix(".snapshot").write_text(json.dumps(snapshot(trace, states)), encoding="utf-8")
            path.with_suffix(".paused").write_text("accepted_batch_before_propagation", encoding="utf-8")
            deadline = time.monotonic() + 45
            while not path.with_suffix(".release").exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError("solver_process_barrier_timeout")
                time.sleep(0.01)

    try:
        e = SimpleNamespace(env=SimpleNamespace(engine=engine, principal=principal), command=command)
        page, trace, states = execute(e, PlanCatalog([entry]), peer, releases, job["run"], after_stage=after_stage)
        path.with_suffix(".reply").write_text(json.dumps({**snapshot(trace, states), "page": page.model_dump(mode="json")}), encoding="utf-8")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
