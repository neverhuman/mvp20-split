"""Persisted graph orchestration through public numeric/evaluator CLI boundaries."""

import json

import pytest
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import SchemaRef
from sqlalchemy import text

from ..bindings.support import MemoryArtifacts
from .catalog import catalog, cli
from .definition import campaign
from .execution import execute
from .specification import specification


@pytest.mark.parametrize("generations,population,evaluations,fixed,fail_member,reason", [
    (0, 1, 20, False, False, "generation_budget"),
    (2, 2, 20, False, False, "generation_budget"),
    (2, 2, 0, False, False, "evaluation_budget"),
    (2, 2, 20, True, False, "generation_budget"),
    (2, 2, 20, False, True, "unavailable_fitness"),
])
def test_numeric_generations_commit_with_explicit_stop_and_evidence(
        graph_env, tmp_path, generations, population, evaluations, fixed, fail_member, reason):
    e = graph_env
    releases, tools, schemas = catalog()
    scope = e.env.principal.scope.model_dump(mode="json")
    raw = campaign(scope, releases, generations)
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), tools, schemas)
    plans = PlanCatalog([entry])
    peer = MemoryArtifacts(e.env.principal.scope)
    policy_schema = releases["evaluate"]["tool"]["inputs"][1]["schema_ref"]
    policy = peer.store(cli("amphora_synthetic_objectives", "policy"), SchemaRef.model_validate(policy_schema))
    spec = specification(scope, releases, policy.model_dump(mode="json"), generations=generations,
                         population=population, evaluations=evaluations, fixed=fixed)
    spec_ref = peer.store(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode(), SchemaRef.model_validate(releases["seed"]["tool"]["inputs"][0]["schema_ref"]))
    references = {"specification": spec_ref, "policy": policy}
    inputs = [{"port": port["name"], "value": {"kind": "artifact", "artifact": references[port["name"]].model_dump(mode="json"),
        "representation": port["value_type"]["representation"], "unit": port["value_type"]["unit"]}} for port in raw["body"]["inputs"]]
    receipt = GraphAdmission(e.env.engine, plans, bindings_enabled=True).admit(e.env.principal, e.command("graph.admit", {
        "plan_sha256": entry.plan.sha256, "inputs": inputs, "budget": {"limit": 256, "max_attempts_per_activation": 1}}))
    assert receipt.outcome.status == "accepted", receipt
    run = receipt.outcome.committed.object_id
    page, trace, states = execute(e, plans, peer, releases, run, tmp_path, fail_member=fail_member)
    assert page.status == "completed", page
    assert page.reserved == 0 and page.spent == len(trace)
    with e.env.engine.connect() as conn:
        outputs = conn.execute(text("SELECT outputs FROM runtime.graph_runs WHERE run_id=:run"), {"run": run}).scalar_one()
    final = json.loads(peer.documents[outputs[0]["value"]["artifact"]["artifact_id"]])
    assert final == states[-1]
    assert final["phase"] == "stopped" and final["stop_reason"] == reason
    evaluated = [item for item in trace if item["stage"] == "evaluate"]
    if evaluations == 0:
        assert not evaluated and final["rng"]["counter"] == population
        assert [state["generation"] for state in states] == [0, 0]
    elif fail_member:
        assert len(evaluated) == population
        assert any(item["outcome"]["status"] == "failed" for item in final["observations"])
        assert final["generation"] == 0
    else:
        assert [state["generation"] for state in states] == list(range(generations + 1))
        assert final["rng"]["counter"] == population * (1 + generations * 6)
        if fixed:
            assert len(evaluated) == 1
        for item in evaluated:
            value = item["input"]["candidate"]["genes"][0]
            outcome = item["result"]["outcome"]
            assert outcome["objectives"][0]["value"] == value * value
            assert outcome["quality"] == "synthetic" and outcome["evidence"] == [policy.model_dump(mode="json")]
        for state in states:
            scores = {item["candidate_id"]: item["outcome"]["objectives"][0]["value"] for item in state["observations"]}
            assert scores[state["population"][0]] == min(scores.values())
