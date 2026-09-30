"""Admission selection is explicit, canonical and separate from save/validation receipts."""

import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import AdmitDraft, parse_graph_command
from pydantic import ValidationError


def payload():
    return {"plan_sha256": "a" * 64, "inputs": [], "budget": {"limit": 3}, "draft": {
        "draft_id": "research", "revision": 2, "content_sha256": "b" * 64,
        "validation_id": "validation", "universe_sha256": "c" * 64}}


def test_draft_admission_requires_every_pin_and_preserves_command_identity():
    raw = {"identity": {"scope": {"tenant_id": "tenant", "project_id": "project"}, "actor_id": "researcher",
        "command_family": "graph.admit_draft", "command_id": "admit-next"}, "payload": payload()}
    command = parse_graph_command("graph.admit_draft", json.dumps(raw))
    assert command.identity.command_id == "admit-next"
    assert json.loads(command.canonical_bytes)["payload"]["draft"] == raw["payload"]["draft"]
    with pytest.raises(CommandEncodingError):
        parse_graph_command("graph.admit", json.dumps(raw))
    for field in tuple(raw["payload"]["draft"]):
        incomplete = payload()
        del incomplete["draft"][field]
        with pytest.raises(ValidationError):
            AdmitDraft.model_validate_json(json.dumps(incomplete))


@pytest.mark.parametrize("revision", [0, -1, 9007199254740992, True])
def test_draft_admission_revision_is_a_positive_safe_integer(revision):
    raw = payload()
    raw["draft"]["revision"] = revision
    with pytest.raises(ValidationError):
        AdmitDraft.model_validate_json(json.dumps(raw))
