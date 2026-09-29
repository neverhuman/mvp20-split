"""Actual graph/worker transactions and fixture kernels; explicitly scripted Artifact owner."""

import json

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_contracts_campaigns import parse_executable_campaign
from sqlalchemy import text

from ..bindings.support import MemoryArtifacts
from .catalog import STAGES, catalog
from .definition import campaign
from .execution import execute
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
    page, trace, states = execute(e, plans, peer, releases, run)
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
