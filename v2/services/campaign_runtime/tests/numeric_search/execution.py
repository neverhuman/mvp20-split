"""Actual Runtime transactions; CLI subprocess tools; explicitly scripted Artifact peer."""

import json
import subprocess
import sys

from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_core import SchemaRef

from .catalog import IMAGE


def execute(e, plans, peer, releases, run, root, *, fail_member=False):
    trace, states = [], []
    for _ in range(160):
        binding = BindingCoordinator(e.env.engine, plans, peer, peer)
        reply = GraphAdvancer(e.env.engine, projections=peer, bindings=binding).advance(e.env.principal, e.command("graph.advance", {"run_id": run}))
        assert reply.outcome.status == "accepted", reply
        page = GraphReads(e.env.engine).run(e.env.principal, run, version=3)
        if page.status != "running":
            return page, trace, states
        for stage, release in releases.items():
            work = []
            for _ in range(8):
                claim = RuntimeLeases(e.env.engine).claim(e.env.principal, e.command("runtime.claim", {
                    "run_id": run, "worker_id": e.env.principal.actor_id,
                    "tool": release["tool"]["binding"], "lease_seconds": 90}))
                if claim.outcome.status != "claimed":
                    break
                work.append(claim.outcome.invocation)
            def parameters(invocation):
                return next(item.artifact for item in invocation.inputs if item.port == "parameters")
            if stage == "evaluate":
                work.sort(key=lambda invocation: json.loads(peer.documents[parameters(invocation).artifact_id])["candidate"]["ordinal"], reverse=True)
            for invocation in work:
                source = peer.documents[parameters(invocation).artifact_id]
                source_data = json.loads(source)
                failure = stage == "evaluate" and fail_member and source_data["candidate"]["ordinal"] == 0
                result = None
                if failure:
                    outcome = {"status": "failed", "reason_code": "synthetic_fixture_failure", "retryable": False}
                else:
                    numeric = stage != "evaluate"
                    module = "amphora_evolution_search" if numeric else "amphora_synthetic_objectives"
                    arguments = ["--operation", stage] if numeric else []
                    if not numeric:
                        policy = next(item.artifact for item in invocation.inputs if item.port == "policy")
                        policy_path = root / "policy.json"
                        policy_path.write_bytes(peer.documents[policy.artifact_id])
                        arguments = ["--policy-file", str(policy_path)]
                    completed = subprocess.run([sys.executable, "-m", module, "compute", *arguments,
                        "--image-sha256", IMAGE], input=source, capture_output=True, check=False)
                    assert completed.returncode == 0, (stage, completed.stderr.decode())
                    result = json.loads(completed.stdout)
                    artifact = peer.store(completed.stdout, SchemaRef.model_validate(release["tool"]["outputs"][0]["schema_ref"]))
                    outcome = {"status": "succeeded", "outputs": [{"port": "result", "artifact": artifact.model_dump(mode="json")}]}
                    if stage == "collect":
                        states.append(result)
                completion = CompletionCoordinator(e.env.engine, peer).complete(e.env.principal, e.command("runtime.complete", {
                    "run_id": run, "completion": {"schema_version": "1", "invocation_id": invocation.invocation_id,
                        "attempt_id": invocation.attempt_id, "fence": invocation.fence, "outcome": outcome}}))
                assert completion.outcome.status == "accepted", completion
                trace.append({"stage": stage, "input": source_data, "result": result, "status": outcome["status"]})
    raise AssertionError("numeric graph exceeded bounded fixture advances")
