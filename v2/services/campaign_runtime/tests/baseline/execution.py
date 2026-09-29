"""Test-only graph controller shared by in-process and killed-process oracles."""

import json

from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases

from .catalog import STAGES


def execute(e, plans, peer, releases, run, *, after_stage=None):
    trace, states = [], []
    for _ in range(100):
        binding = BindingCoordinator(e.env.engine, plans, peer, peer)
        reply = GraphAdvancer(e.env.engine, bindings=binding).advance(e.env.principal, e.command("graph.advance", {"run_id": run}))
        assert reply.outcome.status == "accepted", reply
        page = GraphReads(e.env.engine).run(e.env.principal, run, version=3)
        if page.status != "running":
            break
        for stage, (metadata, kernel) in STAGES.items():
            work = []
            for _ in range(8):
                claim = RuntimeLeases(e.env.engine).claim(e.env.principal, e.command("runtime.claim", {
                    "run_id": run, "worker_id": e.env.principal.actor_id, "tool": releases[stage]["tool"]["binding"], "lease_seconds": 30}))
                if claim.outcome.status != "claimed":
                    break
                work.append(claim.outcome.invocation)
            # Explicit request-index reversal, independent of activation hash/claim order.
            if stage == "score":
                work.sort(key=lambda invocation: json.loads(peer.documents[invocation.inputs[0].artifact.artifact_id])["candidate"]["proposal_index"], reverse=True)
            for invocation in work:
                source = peer.documents[invocation.inputs[0].artifact.artifact_id]
                try:
                    body = kernel.compute(source)
                    artifact = peer.store(body, metadata.schema_ref("output"))
                    outcome = {"status": "succeeded", "outputs": [{"port": "result", "artifact": artifact.model_dump(mode="json")}]}
                    if stage == "retain":
                        states.append(json.loads(body))
                except ValueError as error:
                    assert str(error) in {"synthetic_scoring_failure", "no_successful_candidates"}, str(error)
                    outcome = {"status": "failed", "reason_code": "synthetic_fixture_failure", "retryable": False}
                completion = CompletionCoordinator(e.env.engine, peer).complete(e.env.principal, e.command("runtime.complete", {
                    "run_id": run, "completion": {"schema_version": "1", "invocation_id": invocation.invocation_id,
                        "attempt_id": invocation.attempt_id, "fence": invocation.fence, "outcome": outcome}}))
                assert completion.outcome.status == "accepted", completion
                trace.append({"stage": stage, "input": json.loads(source), "status": outcome["status"]})
            if work and after_stage is not None:
                after_stage(stage, trace, states)
    return page, trace, states
