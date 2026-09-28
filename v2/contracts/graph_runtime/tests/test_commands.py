"""Strict graph wire inputs, scope validation and unchanged worker command namespace."""

import copy
import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import AdmitGraphRun, parse_graph_command
from amphora_contracts_runtime import parse_command
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def request(value=None):
    return {"identity": {"scope": {"tenant_id": "test", "project_id": "graph"}, "actor_id": "owner",
                         "command_family": "graph.admit", "command_id": "admit-1"},
            "payload": {"plan_sha256": "a" * 64, "inputs": [] if value is None else [{"port": "input", "value": value}],
                        "budget": {"limit": 2}}}


@pytest.mark.parametrize("value", [None, {"kind": "integer", "value": 2}, {"kind": "number", "value": "2.5", "unit": "g/mol"},
    {"kind": "boolean", "value": False}, {"kind": "string", "value": "candidate"},
    {"kind": "collection", "items": [{"kind": "integer", "value": 2}, {"kind": "missing", "reason_code": "skipped", "member_id": "m2"}]}])
def test_explicit_values_and_idempotent_command_fingerprints(value):
    raw = request(value)
    original = parse_graph_command("graph.admit", json.dumps(raw))
    assert parse_graph_command("graph.admit", original.canonical_bytes).canonical_bytes == original.canonical_bytes
    decoded = AdmitGraphRun.model_validate_json(json.dumps(raw["payload"]))
    Draft202012Validator(AdmitGraphRun.model_json_schema()).validate(json.loads(decoded.model_dump_json()))
    with pytest.raises(CommandEncodingError, match="unknown_family"):
        parse_command("graph.admit", json.dumps(raw))


@pytest.mark.parametrize("value", [
    {"kind": "input", "name": "hidden"}, {"kind": "output", "node_id": "hidden", "port": "result"},
    {"kind": "object", "payload": {}}, {"kind": "collection", "items": [{"kind": "collection", "items": []}]},
    {"kind": "number", "value": 2.5}, {"kind": "number", "value": "NaN"}, {"kind": "number", "value": "1e999"},
])
def test_input_cannot_reference_uncommitted_or_untyped_values(value):
    with pytest.raises(ValidationError):
        AdmitGraphRun.model_validate_json(json.dumps(request(value)["payload"]))


@pytest.mark.parametrize("collection", [False, True])
def test_artifact_scope_is_checked_before_registration(collection):
    artifact = {"kind": "artifact", "unit": "1", "representation": "synthetic", "artifact": {
        "artifact_id": "a", "scope": {"tenant_id": "wrong", "project_id": "graph"}, "sha256": "b" * 64,
        "schema_ref": {"schema_id": "schema", "version": "1", "sha256": "c" * 64}, "media_type": "application/json", "size_bytes": 2}}
    raw = request({"kind": "collection", "items": [artifact]} if collection else artifact)
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_graph_command("graph.admit", json.dumps(raw))
    artifact["artifact"]["scope"] = copy.deepcopy(raw["identity"]["scope"])
    assert parse_graph_command("graph.admit", json.dumps(raw))


def test_graph_limits_are_finite_and_explicit():
    raw = request()["payload"]
    raw["limits"] = {"max_activations": 0, "deadline_seconds": 0}
    with pytest.raises(ValidationError):
        AdmitGraphRun.model_validate_json(json.dumps(raw))


def test_graph_parser_does_not_relax_existing_command_number_policy():
    with pytest.raises(CommandEncodingError, match="non_integer_number"):
        parse_graph_command("graph.admit", json.dumps(request({"kind": "number", "value": 2.5})))
