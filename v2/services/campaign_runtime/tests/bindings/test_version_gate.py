"""Contract/compiler delivery cannot accidentally authorize incomplete conversion execution."""

import copy
import json

from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_contracts_campaigns import parse_executable_campaign
from sqlalchemy import text

from ..compiler.test_bindings import CASES, catalog


def test_new_profile_is_explicitly_nonexecutable_until_transition_gate(graph_env):
    raw = copy.deepcopy(CASES[1]["payload"])
    raw["scope"] = graph_env.env.principal.scope.model_dump(mode="json")
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), catalog())
    owner = GraphAdmission(graph_env.env.engine, PlanCatalog([entry]))
    command = graph_env.command("graph.admit", {"plan_sha256": entry.plan.sha256, "inputs": [], "budget": {"limit": 2}})
    reply = owner.admit(graph_env.env.principal, command)
    assert reply.outcome.status == "rejected" and reply.outcome.reason_code == "graph_binding_profile_not_enabled"
    assert owner.admit(graph_env.env.principal, command) == reply
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.runs WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": raw["scope"]["tenant_id"], "project": raw["scope"]["project_id"]}).scalar_one() == 0
