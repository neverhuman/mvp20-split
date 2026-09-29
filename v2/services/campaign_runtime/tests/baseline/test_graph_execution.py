"""Actual graph/worker transactions and fixture kernels; explicitly scripted Artifact owner."""

import json

import pytest
from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_campaigns import parse_executable_campaign
from sqlalchemy import text

from ..bindings.support import MemoryArtifacts
from .catalog import STAGES, catalog
from .definition import campaign
from .test_stage_oracles import ORACLES, PINS


@pytest.mark.parametrize("case", ORACLES, ids=[case["name"] for case in ORACLES])
def test_source_population_graph_executes_against_independent_oracle(graph_env, case):
    e = graph_env
    releases, tools, schemas = catalog()
    raw = campaign(e.env.principal.scope.model_dump(mode="json"), releases, case["config"]["generations"])
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), tools, schemas)
    plans = PlanCatalog([entry])
    peer = MemoryArtifacts(e.env.principal.scope)
    seed_ref = peer.put({**case["config"], "source_pins": PINS}, STAGES["seed"][0].schema_ref("input"))
    shape = raw["body"]["inputs"][0]["value_type"]
    admission = GraphAdmission(e.env.engine, plans, bindings_enabled=True).admit(e.env.principal, e.command("graph.admit", {
        "plan_sha256": entry.plan.sha256, "inputs": [{"port": "parameters", "value": {"kind": "artifact", "artifact": seed_ref.model_dump(mode="json"),
            "representation": shape["representation"], "unit": shape["unit"]}}], "budget": {"limit": 100, "max_attempts_per_activation": 1}}))
    assert admission.outcome.status == "accepted", admission
    run = admission.outcome.committed.object_id
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
    assert page.status == case["terminal"], page
    assert page.reserved == 0 and page.spent == len(trace)
    assert [state["generation"] for state in states] == case["checkpoints"]
    for state, expected in zip(states, case["generations"], strict=False):
        assert [item["candidate"]["candidate_id"] for item in state["current"]] == expected["current"]
        assert [item["candidate"]["candidate_id"] for item in state["cumulative"]] == expected["cumulative"]
    scores = [item["input"]["candidate"] for item in trace if item["stage"] == "score"]
    for expected in case["generations"]:
        observed = [item for item in scores if item["generation"] == expected["generation"]]
        assert [item["candidate_id"] for item in observed] == list(reversed(expected["candidate_ids"]))
        assert [item["scoring_seed"] for item in observed] == list(reversed(expected["scoring_seeds"]))
    if page.status == "completed":
        with e.env.engine.connect() as conn:
            output = conn.execute(text("SELECT outputs FROM runtime.graph_runs WHERE run_id=:run"), {"run": run}).scalar_one()
        final = json.loads(peer.documents[output[0]["value"]["artifact"]["artifact_id"]])
        assert final == states[-1]
