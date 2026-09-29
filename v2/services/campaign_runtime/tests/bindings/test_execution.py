"""Actual Runtime transactions with a labeled scripted Artifact peer."""

import copy
import json
from decimal import Decimal

import pytest
from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_contracts_campaigns import parse_executable_campaign
from sqlalchemy import text

from ..compiler.test_bindings import CASES, catalog
from .support import MemoryArtifacts


def setup(e, case, *, timeout=120, source_bytes=None, transform=None):
    raw = copy.deepcopy(CASES[case]["payload"])
    raw["scope"] = e.env.principal.scope.model_dump(mode="json")
    raw["body"]["nodes"][0]["limits"]["timeout_seconds"] = timeout
    if transform is not None:
        transform(raw)
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), catalog())
    plans = PlanCatalog([entry])
    peer = MemoryArtifacts(e.env.principal.scope)
    shape = entry.plan.document.definition.body.inputs[0].value_type
    if case == 4:
        value = {"kind": "collection", "items": [{"kind": "number", "value": "0.123456789012345678901", "unit": "1"},
                                                 {"kind": "number", "value": "-2", "unit": "1"}]}
    else:
        if case in {0, 1}:
            data = {"count": 2, "values": [Decimal("0.123456789012345678901"), -2]}
        elif case == 2:
            data = {"items": [{"id": "second", "value": 5}, {"id": "first", "value": 2}]}
        else:
            member = entry.plan.document.definition.body.nodes[0].output.value_type.item
            data = [peer.put({"id": "second", "value": 5}, member.schema_ref).model_dump(mode="json"),
                    peer.put({"id": "first", "value": 2}, member.schema_ref).model_dump(mode="json")]
        ref = peer.put(data, shape.schema_ref) if source_bytes is None else peer.store(source_bytes, shape.schema_ref)
        value = {"kind": "artifact", "artifact": ref.model_dump(mode="json"), "representation": shape.representation, "unit": shape.unit}
    admission = GraphAdmission(e.env.engine, plans, bindings_enabled=True)
    command = e.command("graph.admit", {"plan_sha256": entry.plan.sha256, "inputs": [{"port": "parameters", "value": value}], "budget": {"limit": 2}})
    reply = admission.admit(e.env.principal, command)
    assert reply.outcome.status == "accepted", reply
    run_id = reply.outcome.committed.object_id
    bindings = BindingCoordinator(e.env.engine, plans, peer, peer)
    advancer = GraphAdvancer(e.env.engine, bindings=bindings)
    return run_id, bindings, advancer, peer


def advance(e, run, advancer):
    command = e.command("graph.advance", {"run_id": run})
    reply = advancer.advance(e.env.principal, command)
    assert reply.outcome.status == "accepted", reply
    assert advancer.advance(e.env.principal, command) == reply


@pytest.mark.parametrize("case", range(5), ids=[item["name"] for item in CASES])
def test_conversion_commits_protected_ordered_outputs_without_attempts(graph_env, case):
    e = graph_env
    run, bindings, advancer, peer = setup(e, case)
    advance(e, run, advancer)
    advance(e, run, advancer)
    observed = GraphReads(e.env.engine).run(e.env.principal, run, version=3)
    assert observed.status == "completed" and observed.spent == observed.reserved == 0, observed
    with e.env.engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM runtime.binding_intents WHERE run_id=:run"), {"run": run}).mappings().one()
        assert row["status"] == "committed" and row["outcome"]["runtime_receipt_id"] == row["intent_id"] + ":closed"
        assert conn.execute(text("SELECT count(*) FROM runtime.activations WHERE run_id=:run"), {"run": run}).scalar_one() == 0
        assert conn.execute(text("SELECT count(*) FROM runtime.binding_closures WHERE run_id=:run"), {"run": run}).scalar_one() == 1
        assert conn.execute(text("SELECT count(*) FROM runtime.binding_reservations WHERE intent_id=:intent"),
                            {"intent": row["intent_id"]}).scalar_one() == len(row["output_bindings"])
    value = row["outputs"][0]["value"]
    if case == 0:
        assert value == {"kind": "integer", "unit": "1", "value": 2}
    elif case == 1:
        assert [item["value"] for item in value["items"]] == ["0.123456789012345678901", "-2"]
    elif case in {2, 3}:
        assert [json.loads(peer.documents[item["artifact"]["artifact_id"]])["id"] for item in value["items"]] == ["second", "first"]
    else:
        assert peer.documents[value["artifact"]["artifact_id"]] == b'{"values":[0.123456789012345678901,-2]}'
    assert not bindings.tick(e.env.principal)
