import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from amphora_contracts_campaign_resources import CampaignInvocationResources, parse_resource_bounded_draft
from amphora_contracts_commands import CommandEncodingError, NUMERIC_ENCODING
from amphora_contracts_graph_runtime import parse_graph_command


def document():
    return {"encoding": NUMERIC_ENCODING, "identity": {
        "scope": {"tenant_id": "tenant", "project_id": "project"}, "actor_id": "owner",
        "command_family": "graph.admit_draft_bounded", "command_id": "bounded"},
        "payload": {"plan_sha256": "a" * 64, "inputs": [], "budget": {"limit": 3},
            "draft": {"draft_id": "draft", "revision": 2, "content_sha256": "b" * 64,
                "validation_id": "validated", "universe_sha256": "c" * 64},
            "resources": {"profile": "campaign-invocation-cap-v1", "max_active_attempts": 1}}}


@pytest.mark.parametrize("cap", [1, 4, 8])
def test_explicit_capacity_and_canonical_replay(cap):
    raw = document()
    raw["payload"]["resources"]["max_active_attempts"] = cap
    command = parse_resource_bounded_draft(json.dumps(raw))
    assert parse_resource_bounded_draft(command.canonical_bytes).canonical_bytes == command.canonical_bytes
    assert json.loads(command.canonical_bytes)["payload"]["resources"]["max_active_attempts"] == cap


@pytest.mark.parametrize("cap", [0, 9, -1, True, False, 1.0, "1", None])
def test_capacity_is_bounded_and_strict(cap):
    with pytest.raises(ValidationError):
        CampaignInvocationResources(profile="campaign-invocation-cap-v1", max_active_attempts=cap)


def test_missing_unknown_and_extra_resources_reject():
    for resources in (None, {}, {"profile": "future", "max_active_attempts": 1},
                      {"profile": "campaign-invocation-cap-v1", "max_active_attempts": 1, "extra": 1}):
        raw = document()
        if resources is None:
            del raw["payload"]["resources"]
        else:
            raw["payload"]["resources"] = resources
        with pytest.raises(CommandEncodingError):
            parse_resource_bounded_draft(json.dumps(raw))


def test_new_family_cannot_enter_legacy_admission_and_legacy_has_no_resources():
    raw = document()
    with pytest.raises(CommandEncodingError):
        parse_graph_command("graph.admit_draft", json.dumps(raw))
    del raw["payload"]["resources"]
    raw["identity"]["command_family"] = "graph.admit_draft"
    command = parse_graph_command("graph.admit_draft", json.dumps(raw))
    assert "resources" not in json.loads(command.canonical_bytes)["payload"]
    with pytest.raises(CommandEncodingError):
        parse_resource_bounded_draft(command.canonical_bytes)


@pytest.mark.parametrize("collection", [False, True])
def test_artifact_scope_is_checked_for_scalar_and_collection(collection):
    raw = document()
    value = {"kind": "artifact", "artifact": {"artifact_id": "input",
        "scope": {"tenant_id": "foreign", "project_id": "project"}, "sha256": "a" * 64,
        "size_bytes": 1, "media_type": "application/json",
        "schema_ref": {"schema_id": "test", "version": "1", "sha256": "b" * 64}},
        "representation": "test", "unit": "1"}
    raw["payload"]["inputs"] = [{"port": "input", "value": {"kind": "collection", "items": [value]} if collection else value}]
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_resource_bounded_draft(json.dumps(raw))


def test_command_goldens_pin_new_and_predecessor_bytes():
    fixtures = Path(__file__).parent / "fixtures"
    raw = document()
    assert parse_resource_bounded_draft(json.dumps(raw)).canonical_bytes == (fixtures / "bounded.json").read_bytes()
    del raw["payload"]["resources"]
    raw["identity"]["command_family"] = "graph.admit_draft"
    assert parse_graph_command("graph.admit_draft", json.dumps(raw)).canonical_bytes == (fixtures / "legacy.json").read_bytes()
