"""Await-enabled admission preserves old observation schemas through explicit versions."""

import json

import pytest
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import GraphAdmission, GraphReads, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_campaigns import parse_executable_campaign
from export_schemas import ROOT
from sqlalchemy import text


def test_new_profile_admission_replays_and_requires_versioned_observation(graph_env):
    raw = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[0]["payload"]
    raw["scope"] = graph_env.env.principal.scope.model_dump(mode="json")
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), graph_env.source.schemas)
    command = graph_env.command("graph.admit", {**graph_env.payload, "plan_sha256": entry.plan.sha256})
    service = GraphAdmission(graph_env.env.engine, PlanCatalog([entry]))
    result = service.admit(graph_env.env.principal, command)
    assert result.outcome.status == "accepted"
    assert service.admit(graph_env.env.principal, command) == result
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.runs WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": raw["scope"]["tenant_id"], "project": raw["scope"]["project_id"]}).scalar_one() == 1
    run = result.outcome.committed.object_id
    reads = GraphReads(graph_env.env.engine)
    with pytest.raises(TransitionError, match="graph_observation_v2_required"):
        reads.run(graph_env.env.principal, run)
    assert reads.run(graph_env.env.principal, run, version=2).schema_version == "2"
