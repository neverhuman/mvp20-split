"""Two independently admitted runs preserve the source-derived two-generation oracle."""

import json

from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.successors.reads import SuccessorReads
from amphora_contracts_campaigns import parse_executable_campaign

from ..bindings.support import MemoryArtifacts
from .catalog import STAGES, catalog
from .definition import campaign
from .execution import execute
from .test_stage_oracles import ORACLES, PINS


def test_initial_population_then_successor_generations(graph_env):
    e = graph_env
    case = next(case for case in ORACLES if case["name"] == "two_generations")
    releases, tools, schemas = catalog()
    scope = e.env.principal.scope.model_dump(mode="json")
    initial = campaign(scope, releases, 0)
    continuation = campaign(scope, releases, 2, continuation=True)
    entries = [ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), tools, schemas) for raw in (initial, continuation)]
    plans = PlanCatalog(entries)
    peer = MemoryArtifacts(e.env.principal.scope)
    seed = peer.put({**case["config"], "source_pins": PINS}, STAGES["seed"][0].schema_ref("input"))
    shape = initial["body"]["inputs"][0]["value_type"]
    service = GraphAdmission(e.env.engine, plans, bindings_enabled=True)
    command = e.command("graph.admit", {"plan_sha256": entries[0].plan.sha256, "inputs": [{"port": "parameters",
        "value": {"kind": "artifact", "artifact": seed.model_dump(mode="json"), "representation": shape["representation"], "unit": shape["unit"]}}],
        "budget": {"limit": 100}})
    receipt = service.admit(e.env.principal, command)
    first = receipt.outcome.committed.object_id
    page, trace, states = execute(e, plans, peer, releases, first)
    assert page.status == "completed" and [state["generation"] for state in states] == [0]
    reads = SuccessorReads(e.env.engine)
    cut = reads.sources(e.env.principal, first)
    assert cut.predecessor_ready
    source = cut.sources[0]
    next_command = e.command("graph.admit_successor", {"plan_sha256": entries[1].plan.sha256, "inputs": [], "budget": {"limit": 100},
        "predecessor": cut.predecessor.model_dump(mode="json"), "carried": [{"target_port": "parameters",
            "source": source.source.model_dump(mode="json"), "expected_value_sha256": source.value_sha256}]})
    accepted = service.admit_successor(e.env.principal, next_command)
    assert accepted.outcome.status == "accepted", accepted
    second = accepted.outcome.committed.object_id
    final, next_trace, next_states = execute(e, plans, peer, releases, second)
    assert final.status == "completed" and [state["generation"] for state in next_states] == [1, 2]
    assert "seed" not in [item["stage"] for item in next_trace]
    states += next_states
    trace += next_trace
    for state, expected in zip(states, case["generations"], strict=True):
        assert [item["candidate"]["candidate_id"] for item in state["current"]] == expected["current"]
        assert [item["candidate"]["candidate_id"] for item in state["cumulative"]] == expected["cumulative"]
        scores = [item["input"]["candidate"] for item in trace if item["stage"] == "score" and item["input"]["candidate"]["generation"] == expected["generation"]]
        assert [item["scoring_seed"] for item in scores] == list(reversed(expected["scoring_seeds"]))
        if expected["generation"]:
            assert [item["parent_ids"][0] for item in scores] == list(reversed(expected["parent_ids"]))
    assert service.admit(e.env.principal, command) == receipt
    assert service.admit_successor(e.env.principal, next_command) == accepted
    assert GraphReads(e.env.engine).run(e.env.principal, first, version=3) == page
    assert reads.lineage(e.env.principal, second).predecessor == cut.predecessor
