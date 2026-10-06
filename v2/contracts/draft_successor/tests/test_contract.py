import copy
import json

import pytest
from amphora_contracts_commands import CommandEncodingError, NUMERIC_ENCODING
from amphora_contracts_draft_successor import parse_draft_successor
from amphora_contracts_graph_runtime import parse_graph_command


def document():
    return {"encoding": NUMERIC_ENCODING, "identity": {"scope": {"tenant_id": "tenant", "project_id": "project"}, "actor_id": "owner",
                         "command_family": "graph.admit_draft_successor", "command_id": "next"},
            "payload": {"plan_sha256": "a" * 64, "inputs": [], "budget": {"limit": 3},
                        "draft": {"draft_id": "draft", "revision": 2, "content_sha256": "b" * 64,
                                  "validation_id": "validated", "universe_sha256": "c" * 64},
                        "predecessor": {"run_id": "parent", "plan_sha256": "d" * 64, "revision": 4},
                        "carried": [{"target_port": "value", "source": {"kind": "run_output", "port": "value"},
                                     "expected_value_sha256": "e" * 64}]}}


def test_additive_command_replays_and_cannot_enter_old_families():
    raw = document()
    command = parse_draft_successor(json.dumps(raw))
    assert parse_draft_successor(command.canonical_bytes).canonical_bytes == command.canonical_bytes
    for family in ("graph.admit", "graph.admit_draft", "graph.admit_successor"):
        with pytest.raises(CommandEncodingError):
            parse_graph_command(family, json.dumps(raw))


@pytest.mark.parametrize("field", ["draft", "predecessor", "carried"])
def test_missing_bindings_reject(field):
    raw = document()
    del raw["payload"][field]
    with pytest.raises(CommandEncodingError):
        parse_draft_successor(json.dumps(raw))


def test_duplicate_targets_reject():
    raw = document()
    raw["payload"]["carried"] *= 2
    with pytest.raises(CommandEncodingError, match="duplicate_carried_target"):
        parse_draft_successor(json.dumps(raw))


@pytest.mark.parametrize("value", [0.25, -1.5, 1.0])
def test_numeric_profile_roundtrip(value):
    raw = document()
    raw["payload"]["inputs"] = [{"port": "fresh", "value": {"kind": "number", "value": str(value)}}]
    command = parse_draft_successor(json.dumps(raw))
    assert parse_draft_successor(command.canonical_bytes).canonical_bytes == command.canonical_bytes


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_reject(value):
    raw = document()
    raw["payload"]["inputs"] = [{"port": "fresh", "value": {"kind": "number", "value": value}}]
    with pytest.raises(CommandEncodingError):
        parse_draft_successor(json.dumps(raw))


@pytest.mark.parametrize("collection", [False, True])
def test_foreign_artifact_input_reject(collection):
    raw = document()
    value = {"kind": "artifact", "artifact": {"artifact_id": "input", "scope": {"tenant_id": "foreign", "project_id": "project"},
             "sha256": "a" * 64, "size_bytes": 1, "media_type": "application/json",
             "schema_ref": {"schema_id": "test", "version": "1", "sha256": "b" * 64}},
             "representation": "test", "unit": "1"}
    raw["payload"]["inputs"] = [{"port": "fresh", "value": {"kind": "collection", "items": [value]} if collection else value}]
    with pytest.raises(CommandEncodingError):
        parse_draft_successor(json.dumps(raw))


def test_missing_draft_pin_and_wrong_command_identity_reject():
    for key in document()["payload"]["draft"]:
        raw = document()
        del raw["payload"]["draft"][key]
        with pytest.raises(CommandEncodingError):
            parse_draft_successor(json.dumps(raw))
    raw = copy.deepcopy(document())
    raw["identity"]["command_family"] = "graph.admit_draft"
    with pytest.raises(CommandEncodingError):
        parse_draft_successor(json.dumps(raw))
