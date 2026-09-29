"""Actual Runtime graph/worker transactions; tool kernel in process, Artifact peer scripted."""

import json

from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_numeric_affine.kernel import compute
from sqlalchemy import text

from .definitions import dynamic_graph
from .support import MemoryArtifacts


def test_generated_population_scatter_gather_consumer_and_next_generation(graph_env):
    e = graph_env
    raw = dynamic_graph(e.raw)
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), e.source.tools, e.source.schemas)
    catalog = PlanCatalog([entry])
    peer = MemoryArtifacts(e.env.principal.scope)
    seed = peer.put({"values": [1, 2, 3], "a": 1, "b": 0}, entry.descriptors[0].inputs[0].schema_ref)
    shape = raw["body"]["inputs"][0]["value_type"]
    reply = GraphAdmission(e.env.engine, catalog, bindings_enabled=True).admit(e.env.principal, e.command("graph.admit", {
        "plan_sha256": entry.plan.sha256, "inputs": [{"port": "parameters", "value": {"kind": "artifact", "artifact": seed.model_dump(mode="json"),
        "representation": shape["representation"], "unit": shape["unit"]}}], "budget": {"limit": 20}}))
    assert reply.outcome.status == "accepted", reply
    run = reply.outcome.committed.object_id
    completed = []
    pending_scores, reversed_batches = [], []
    for _ in range(100):
        # Fresh owner objects every pass; persisted state alone determines the next action.
        bindings = BindingCoordinator(e.env.engine, catalog, peer, peer)
        advancer = GraphAdvancer(e.env.engine, bindings=bindings)
        advance = advancer.advance(e.env.principal, e.command("graph.advance", {"run_id": run}))
        assert advance.outcome.status == "accepted", advance
        page = GraphReads(e.env.engine).run(e.env.principal, run, version=3)
        if page.status != "running":
            break
        work = []
        for _ in range(3):
            claim = RuntimeLeases(e.env.engine).claim(e.env.principal, e.command("runtime.claim", {
                "run_id": run, "worker_id": e.env.principal.actor_id, "tool": entry.descriptors[0].binding.model_dump(mode="json"), "lease_seconds": 30}))
            if claim.outcome.status != "claimed":
                break
            work.append(claim.outcome.invocation)
        ordinary = [invocation for invocation in work if invocation.node_id != "score"]
        pending_scores.extend(invocation for invocation in work if invocation.node_id == "score")
        scoring = []
        if len(pending_scores) == 3:
            scoring = sorted(pending_scores, key=lambda invocation: json.loads(
                peer.documents[invocation.inputs[0].artifact.artifact_id])["values"][0], reverse=True)
            reversed_batches.append([json.loads(peer.documents[invocation.inputs[0].artifact.artifact_id])["values"][0]
                                     for invocation in scoring])
            pending_scores = []
        for invocation in [*ordinary, *scoring]:
            result = peer.store(compute(peer.documents[invocation.inputs[0].artifact.artifact_id]), entry.descriptors[0].outputs[0].schema_ref)
            receipt = CompletionCoordinator(e.env.engine, peer).complete(e.env.principal, e.command("runtime.complete", {
                "run_id": run, "completion": {"schema_version": "1", "invocation_id": invocation.invocation_id,
                "attempt_id": invocation.attempt_id, "fence": invocation.fence, "outcome": {"status": "succeeded", "outputs": [
                    {"port": "result", "artifact": result.model_dump(mode="json")}]}}}))
            assert receipt.outcome.status == "accepted", receipt
            completed.append(invocation.node_id)
    assert page.status == "completed", page
    assert page.spent == 10 and page.reserved == 0
    assert completed.count("producer") == completed.count("consumer") == 2 and completed.count("score") == 6
    assert reversed_batches == [[3, 2, 1], [7, 5, 3]]
    with e.env.engine.connect() as conn:
        outputs = conn.execute(text("SELECT outputs FROM runtime.graph_runs WHERE run_id=:run"), {"run": run}).scalar_one()
        counts = conn.execute(text("SELECT status,count(*) FROM runtime.binding_intents WHERE run_id=:run GROUP BY status"), {"run": run}).all()
    assert json.loads(peer.documents[outputs[0]["value"]["artifact"]["artifact_id"]]) == {"a": 1, "b": 0, "values": [7, 11, 15]}
    assert counts == [("committed", 20)]
