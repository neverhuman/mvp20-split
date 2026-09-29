"""Additive successor wire profile: bounded explicit selectors, no mutable references."""

import copy
import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import SuccessorProposal, parse_graph_command
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def proposal():
    return {"plan_sha256": "b" * 64, "inputs": [], "budget": {"limit": 3},
        "predecessor": {"run_id": "parent", "plan_sha256": "a" * 64, "revision": 3},
        "carried": [{"target_port": "state", "source": {"kind": "run_output", "port": "state"},
                     "expected_value_sha256": "c" * 64}]}


@pytest.mark.parametrize("node", [False, True])
def test_successor_command_roundtrip_and_jsonschema(node):
    raw = proposal()
    if node:
        raw["carried"][0]["source"] = {"kind": "node_output", "activation_id": "d" * 64, "port": "state"}
    model = SuccessorProposal.model_validate_json(json.dumps(raw))
    Draft202012Validator(SuccessorProposal.model_json_schema()).validate(json.loads(model.model_dump_json()))
    envelope = {"identity": {"scope": {"tenant_id": "test", "project_id": "successors"}, "actor_id": "owner",
        "command_family": "graph.admit_successor", "command_id": "successor-1"}, "payload": raw}
    parsed = parse_graph_command("graph.admit_successor", json.dumps(envelope))
    assert parse_graph_command("graph.admit_successor", parsed.canonical_bytes).canonical_bytes == parsed.canonical_bytes
    wrong = copy.deepcopy(envelope)
    wrong["identity"]["command_family"] = "graph.admit"
    with pytest.raises(CommandEncodingError):
        parse_graph_command("graph.admit", json.dumps(wrong))


@pytest.mark.parametrize("case", ["negative", "revision_bool", "missing_hash", "dynamic_source", "too_many"])
def test_invalid_transfer_wire_shape(case):
    raw = proposal()
    if case == "negative":
        raw["predecessor"]["revision"] = -1
    elif case == "revision_bool":
        raw["predecessor"]["revision"] = True
    elif case == "missing_hash":
        del raw["carried"][0]["expected_value_sha256"]
    elif case == "dynamic_source":
        raw["carried"][0]["source"]["kind"] = "latest"
    else:
        raw["carried"] *= 65
    with pytest.raises(ValidationError):
        SuccessorProposal.model_validate_json(json.dumps(raw))
