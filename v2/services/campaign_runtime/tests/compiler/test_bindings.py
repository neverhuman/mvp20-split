"""Independent typed conversion interface/order oracles; compilation has no I/O authority."""

import copy
import hashlib
import json

import pytest
from amphora_campaign_runtime.compiler import (
    CompilationError,
    PinnedSchema,
    SchemaCatalog,
    SchemaIdentity,
    ToolCatalog,
    compile_campaign,
)
from amphora_contracts_campaigns import parse_executable_campaign, parse_execution_plan
from amphora_contracts_core import ArtifactRef, SchemaRef
from export_schemas import ROOT

FOLDER = ROOT / "contracts/fixtures/v4"
CASES = [item for item in json.loads((FOLDER / "binding_cases.json").read_bytes()) if item["valid"]]


def catalog(extra=()):
    return SchemaCatalog([*[PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate_json(json.dumps(item["schema_ref"]))),
        (FOLDER / item["path"]).read_bytes()) for item in json.loads((FOLDER / "schemas.json").read_bytes())], *extra])


def compile_raw(raw):
    return compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), catalog())


@pytest.mark.parametrize("case", CASES, ids=lambda item: item["name"])
def test_independent_conversion_interfaces_and_profiles(case):
    raw = case["payload"]
    plan = compile_raw(raw)
    input_name = "values" if case["name"] == "materialize" else "source"
    expected = {"path": [], "order": ["convert", "finish"], "nodes": [
        {"node_id": "convert", "inputs": [{"name": input_name, "value_type": raw["body"]["inputs"][0]["value_type"]}],
         "outputs": raw["body"]["outputs"]},
        {"node_id": "finish", "inputs": raw["body"]["outputs"], "outputs": raw["body"]["outputs"]}]}
    assert plan.document.scopes[0].model_dump(mode="json") == expected
    assert plan.document.profile == "amphora-execution-plan-v3"
    assert plan.document.lock.compiler_profile == "amphora-deterministic-compiler-v3"
    assert not plan.document.lock.tools
    assert parse_execution_plan(plan.model_dump_json()) == plan
    reordered = copy.deepcopy(raw)
    reordered["body"]["nodes"].reverse()
    assert compile_raw(reordered) == plan


@pytest.mark.parametrize("case,change,reason", [
    (1, lambda node: node.update(path=["absent"]), "unknown_projection_property"),
    (1, lambda node: node.update(mode="references"), "binding_artifact_items_required"),
    (1, lambda node: node["output"]["value_type"].update(max_items=2), "binding_member_bound"),
    (1, lambda node: node["output"]["value_type"]["item"].update(unit="kg"), "binding_projection_unit"),
    (1, lambda node: node["output"]["value_type"].update(missing_slots=True), "binding_project_collection_required"),
    (2, lambda node: node["limits"].update(max_artifacts=2), "binding_artifact_bound"),
    (4, lambda node: node["fields"].append(copy.deepcopy(node["fields"][0])), "duplicate_materialize_field"),
    (4, lambda node: node["fields"][0].update(name="unknown"), "binding_materialize_fields"),
    (4, lambda node: node["fields"][0].update(mode="references"), "binding_reference_source_required"),
])
def test_invalid_semantics_fail_before_io(case, change, reason):
    raw = copy.deepcopy(CASES[case]["payload"])
    change(raw["body"]["nodes"][0])
    with pytest.raises(CompilationError, match=reason):
        compile_raw(raw)


def output_schema(raw, document):
    body = json.dumps(document, sort_keys=True).encode()
    identity = SchemaIdentity("fixture.binding-output", "1", hashlib.sha256(body).hexdigest())
    for port in (raw["body"]["outputs"][0], raw["body"]["nodes"][0]["output"]):
        port["value_type"]["schema_ref"] = identity.record()
    return catalog((PinnedSchema(identity, body),))


@pytest.mark.parametrize("item_type,maximum", [("string", 3), ("number", 2)])
def test_impossible_materialized_collection_schema_rejects(item_type, maximum):
    raw = copy.deepcopy(CASES[4]["payload"])
    schemas = output_schema(raw, {"type": "object", "properties": {"values": {
        "type": "array", "items": {"type": item_type}, "maxItems": maximum}}, "required": ["values"]})
    with pytest.raises(CompilationError, match="binding_materialize"):
        compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)


def test_materialized_scalar_field_types_and_field_order_are_explicit():
    raw = copy.deepcopy(CASES[4]["payload"])
    raw["body"]["nodes"][0]["fields"].append({"name": "count", "mode": "inline", "source": {
        "kind": "integer", "value": 3, "unit": "1"}})
    document = {"type": "object", "properties": {"values": {"type": "array", "items": {"type": "number"},
        "maxItems": 3}, "count": {"type": "integer"}}, "required": ["values", "count"]}
    schemas = output_schema(raw, document)
    plan = compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)
    assert [port.name for port in plan.document.scopes[0].nodes[0].inputs] == ["count", "values"]
    raw["body"]["nodes"][0]["fields"].reverse()
    assert compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas) == plan
    raw["body"]["nodes"][0]["fields"][0]["source"] = {"kind": "string", "value": "three"}
    with pytest.raises(CompilationError, match="binding_materialize_type"):
        compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)


def test_empty_projected_collection_preserves_explicit_zero_bound():
    raw = copy.deepcopy(CASES[1]["payload"])
    doc = {"type": "object", "properties": {"values": {"type": "array", "items": {"type": "number"}, "maxItems": 0}},
        "required": ["values"]}
    body = json.dumps(doc).encode()
    identity = SchemaIdentity("fixture.empty-source", "1", hashlib.sha256(body).hexdigest())
    raw["body"]["inputs"][0]["value_type"]["schema_ref"] = identity.record()
    raw["body"]["nodes"][0]["output"]["value_type"]["max_items"] = 0
    raw["body"]["outputs"][0]["value_type"]["max_items"] = 0
    plan = compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), catalog((PinnedSchema(identity, body),)))
    assert plan.document.scopes[0].nodes[0].outputs[0].value_type.max_items == 0


@pytest.mark.parametrize("missing", [False, True])
def test_reference_materialization_keeps_declared_slots(missing):
    raw = copy.deepcopy(CASES[4]["payload"])
    collection = raw["body"]["inputs"][0]["value_type"]
    collection["item"] = copy.deepcopy(CASES[2]["payload"]["body"]["outputs"][0]["value_type"]["item"])
    collection["missing_slots"] = missing
    raw["body"]["nodes"][0]["fields"][0]["mode"] = "references"
    reference = ArtifactRef.model_json_schema()
    definitions = reference.pop("$defs", {})
    absent = {"type": "object", "properties": {"kind": {"const": "missing"},
        "member_id": {"type": "string"}, "reason_code": {"type": "string"}},
        "required": ["kind", "member_id", "reason_code"]}
    item = {"anyOf": [reference, absent]} if missing else reference
    document = {"type": "object", "$defs": definitions, "properties": {"values": {
        "type": "array", "items": item, "maxItems": 3}}, "required": ["values"]}
    schemas = output_schema(raw, document)
    plan = compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)
    assert plan.document.scopes[0].nodes[0].inputs[0].value_type.model_dump(mode="json") == collection
    if missing:
        document["properties"]["values"]["items"] = reference
        schemas = output_schema(raw, document)
        with pytest.raises(CompilationError, match="binding_materialize_missing_schema"):
            compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), schemas)
