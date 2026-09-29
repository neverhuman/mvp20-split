"""Malformed/foreign content cannot become accepted graph membership."""

import copy
import json

import pytest
from amphora_campaign_runtime.compiler import ToolCatalog
from amphora_campaign_runtime.coordinator import (
    GraphAdmission,
    PlanCatalog,
    ReviewedPlan,
)
from amphora_contracts_campaigns import parse_executable_campaign
from amphora_contracts_commands import CommandEncodingError
from sqlalchemy import text

from ..compiler.test_bindings import CASES, catalog
from ..scheduling.test_projections import artifact_http as artifact_http
from .test_execution import advance, setup
from .test_recovery import intent


@pytest.mark.parametrize("case,body,reason", [
    ("hash", None, "projection_artifact_integrity"),
    ("metadata", None, "projection_artifact_binding_mismatch"),
    ("oversize", None, "projection_payload_too_large"),
    ("duplicate", b'{"values":[1],"values":[2],"count":1}', "projection_artifact_json_invalid"),
    ("nonfinite", b'{"values":[NaN],"count":1}', "projection_artifact_json_invalid"),
    ("type", b'{"values":["wrong"],"count":1}', "binding_schema_invalid"),
    ("malformed", b'{"values":', "projection_artifact_json_invalid"),
])
def test_public_read_failures_never_expose_partial_outputs(graph_env, artifact_http, case, body, reason):
    e, state = graph_env, artifact_http
    run, bindings, advancer, peer = setup(e, 1, source_bytes=body)
    advance(e, run, advancer)
    source = intent(e, run)["inputs"][0]["value"]["artifact"]
    state["metadata"] = source
    state["body"] = peer.documents[source["artifact_id"]]
    if case == "hash":
        state["body"] = b'x' * len(state["body"])
    elif case == "metadata":
        state["metadata"] = {**source, "artifact_id": "wrong"}
    elif case == "oversize":
        state["body"] = b'x' * 262145
    peer.reader = state["client"]
    bindings.tick(e.env.principal)
    row = intent(e, run)
    assert row["status"] == "aborted" and row["outputs"] is None
    assert row["outcome"]["reason_code"] == reason
    with e.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_nodes WHERE run_id=:run AND outputs IS NOT NULL"),
                            {"run": run}).scalar_one() == 0


@pytest.mark.parametrize("mutation", ["unit", "representation", "schema", "scope"])
def test_admission_rejects_typed_source_changes_before_conversion(graph_env, mutation):
    e = graph_env
    raw = copy.deepcopy(CASES[1]["payload"])
    raw["scope"] = e.env.principal.scope.model_dump(mode="json")
    shape = raw["body"]["inputs"][0]["value_type"]
    entry = ReviewedPlan.compile(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), catalog())
    value = {"kind": "artifact", "representation": shape["representation"], "unit": shape["unit"], "artifact": {
        "artifact_id": "input", "scope": raw["scope"], "schema_ref": copy.deepcopy(shape["schema_ref"]),
        "media_type": "application/json", "sha256": "a" * 64, "size_bytes": 2}}
    if mutation in {"unit", "representation"}:
        value[mutation] = "different"
    elif mutation == "scope":
        value["artifact"]["scope"] = {"tenant_id": "foreign", "project_id": "foreign"}
    else:
        value["artifact"]["schema_ref"]["sha256"] = "b" * 64
    payload = {"plan_sha256": entry.plan.sha256, "inputs": [{"port": "parameters", "value": value}], "budget": {"limit": 1}}
    if mutation == "scope":
        with pytest.raises(CommandEncodingError, match="scope_mismatch"):
            e.command("graph.admit", payload)
        return
    reply = GraphAdmission(e.env.engine, PlanCatalog([entry]), bindings_enabled=True).admit(
        e.env.principal, e.command("graph.admit", payload))
    assert reply.outcome.status == "rejected" and reply.outcome.reason_code == "graph_input_type_mismatch"


@pytest.mark.parametrize("nested", [False, True])
def test_reference_manifest_cannot_grant_foreign_or_nested_authority(graph_env, nested):
    e = graph_env
    member_shape = CASES[3]["payload"]["body"]["nodes"][0]["output"]["value_type"]["item"]
    foreign = {"artifact_id": "foreign", "scope": {"tenant_id": "foreign", "project_id": "foreign"},
        "schema_ref": member_shape["schema_ref"], "media_type": "application/json", "size_bytes": 2, "sha256": "a" * 64}
    body = json.dumps([{"nested": foreign} if nested else foreign]).encode()
    run, bindings, advancer, peer = setup(e, 3, source_bytes=body)
    advance(e, run, advancer)
    bindings.tick(e.env.principal)
    row = intent(e, run)
    assert row["status"] == "aborted" and row["outputs"] is None
    assert set(peer.reservations) == {"source"}
    assert row["outcome"]["reason_code"] == ("binding_schema_invalid" if nested else "binding_artifact_scope_or_media")


@pytest.mark.parametrize("boundary", ["before_claim", "during_publish"])
def test_changed_predecessor_cut_cannot_be_accepted(graph_env, boundary):
    e = graph_env

    def chain(raw):
        materialize = copy.deepcopy(CASES[4]["payload"]["body"]["nodes"][0])
        materialize["node_id"] = "pack"
        materialize["fields"][0]["source"] = {"kind": "output", "node_id": "convert", "port": "result"}
        raw["body"]["nodes"].insert(1, materialize)
        raw["body"]["nodes"][-1]["outputs"][0]["source"]["node_id"] = "pack"
        raw["body"]["outputs"] = [materialize["output"]]
        raw["body"]["edges"] = [{"source": a, "target": b, "route": "next"}
                                 for a, b in (("convert", "pack"), ("pack", "finish"))]

    run, bindings, advancer, peer = setup(e, 1, transform=chain)
    advance(e, run, advancer)
    advance(e, run, advancer)

    def pending():
        with e.env.engine.connect() as conn:
            return conn.execute(text("SELECT * FROM runtime.binding_intents WHERE run_id=:run AND node->>'node_id'='pack'"),
                                {"run": run}).mappings().one()

    original = pending()
    assert original["status"] == "prepared"

    def corrupt():
        # Explicit owner-state fault injection, not an allowed graph edit API.
        with e.env.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.graph_nodes SET outputs=jsonb_set(outputs,'{0,value,items,0,value}', '\"99\"') "
                              "WHERE run_id=:run AND node_id='convert'"), {"run": run})

    if boundary == "before_claim":
        corrupt()
    else:
        publish = peer.publish

        def interrupted_publish(*args):
            result = publish(*args)
            corrupt()
            return result

        peer.publish = interrupted_publish
    bindings.tick(e.env.principal)
    row = pending()
    assert row["status"] == "aborted" and row["outputs"] is None
    assert row["outcome"]["reason_code"] == "binding_source_cut_changed"
    assert row["inputs"] == original["inputs"] and row["semantic_sha256"] == original["semantic_sha256"]
    advance(e, run, advancer)
