"""Independent Artifact-field and missing-slot materialization oracles."""

import copy
import json

import pytest
from amphora_campaign_runtime.artifact_bindings.coordinator import BindingCoordinator
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from ..compiler.test_bindings import CASES, FOLDER, output_schema
from .support import MemoryArtifacts
from .test_execution import advance


@pytest.mark.parametrize("mode", ["inline", "references"])
@pytest.mark.parametrize("slots", ["present", "mixed", "missing", "empty"])
def test_artifact_fields_and_missing_slots_preserve_exact_order(graph_env, mode, slots):
    e = graph_env
    raw = copy.deepcopy(CASES[4]["payload"])
    raw["scope"] = e.env.principal.scope.model_dump(mode="json")
    node = raw["body"]["nodes"][0]
    node["fields"][0]["mode"] = mode
    item_shape = copy.deepcopy(CASES[2]["payload"]["body"]["outputs"][0]["value_type"]["item"])
    raw["body"]["inputs"][0]["value_type"].update(item=item_shape, missing_slots=True)
    member_schema = json.loads((FOLDER / "member.schema.json").read_bytes()) if mode == "inline" else ArtifactRef.model_json_schema()
    definitions = member_schema.pop("$defs", {})
    missing_schema = {"type": "object", "properties": {"kind": {"const": "missing"},
        "member_id": {"type": "string"}, "reason_code": {"type": "string"}}, "required": ["kind", "member_id", "reason_code"]}
    schemas = output_schema(raw, {"type": "object", "$defs": definitions, "properties": {"values": {"type": "array",
        "items": {"anyOf": [member_schema, missing_schema]}, "maxItems": 3}}, "required": ["values"]})
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)
    catalog = PlanCatalog([entry])
    peer = MemoryArtifacts(e.env.principal.scope)
    member = peer.put({"id": "candidate", "value": 7}, entry.plan.document.definition.body.inputs[0].value_type.item.schema_ref)
    present = {"kind": "artifact", "artifact": member.model_dump(mode="json"), "representation": item_shape["representation"], "unit": "1"}
    missing = {"kind": "missing", "member_id": "absent", "reason_code": "tool_abstained"}
    values = {"present": [present], "mixed": [missing, present], "missing": [missing], "empty": []}[slots]
    reply = GraphAdmission(e.env.engine, catalog, bindings_enabled=True).admit(e.env.principal, e.command("graph.admit", {
        "plan_sha256": entry.plan.sha256, "inputs": [{"port": "parameters", "value": {"kind": "collection", "items": values}}], "budget": {"limit": 1}}))
    assert reply.outcome.status == "accepted", reply
    run = reply.outcome.committed.object_id
    advancer = GraphAdvancer(e.env.engine, bindings=BindingCoordinator(e.env.engine, catalog, peer, peer))
    advance(e, run, advancer)
    advance(e, run, advancer)
    with e.env.engine.connect() as conn:
        row = conn.execute(text("SELECT status,outputs FROM runtime.binding_intents WHERE run_id=:run"), {"run": run}).mappings().one()
    assert row["status"] == "committed", row
    result = json.loads(peer.documents[row["outputs"][0]["value"]["artifact"]["artifact_id"]])
    expected_present = {"id": "candidate", "value": 7} if mode == "inline" else member.model_dump(mode="json")
    assert result == {"values": [missing if value["kind"] == "missing" else expected_present for value in values]}
