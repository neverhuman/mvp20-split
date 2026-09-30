"""Authoring DTOs preserve separate draft, validation and execution authority."""

import json

import pytest
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_graph_runtime import (
    DraftCommandReceipt,
    DraftRevision,
    DraftValidation,
    SaveDraft,
    parse_authoring_command,
    parse_graph_command,
)
from amphora_contracts_runtime import CommandReceipt
from jsonschema import Draft202012Validator
from pydantic import ValidationError

SCOPE = {"tenant_id": "test", "project_id": "drafts"}


def definition():
    return {"schema_version": "4", "profile": "deterministic-v3", "campaign_id": "research", "revision": 1,
        "scope": SCOPE.copy(), "body": {"nodes": [{"kind": "finish", "node_id": "done", "outputs": []}]}}


def request():
    return {"identity": {"scope": SCOPE.copy(), "actor_id": "editor", "command_family": "definition.save", "command_id": "save-1"},
        "payload": {"draft_id": "draft-1", "expected_revision": 0, "title": "New campaign", "definition": definition()}}


def test_save_is_canonical_and_not_an_execution_command():
    raw = request()
    command = parse_authoring_command("definition.save", json.dumps(raw))
    assert parse_authoring_command("definition.save", command.canonical_bytes).canonical_bytes == command.canonical_bytes
    dto = SaveDraft.model_validate_json(json.dumps(raw["payload"]))
    Draft202012Validator(SaveDraft.model_json_schema()).validate(json.loads(dto.model_dump_json()))
    with pytest.raises(CommandEncodingError, match="unknown_family"):
        parse_graph_command("definition.save", json.dumps(raw))
    with pytest.raises(CommandEncodingError, match="unknown_family"):
        parse_authoring_command("graph.admit", json.dumps(raw))


@pytest.mark.parametrize("revision", [-1, True, "0", 9007199254740992])
def test_save_requires_exact_bounded_revision(revision):
    raw = request()["payload"]
    raw["expected_revision"] = revision
    with pytest.raises(ValidationError):
        SaveDraft.model_validate_json(json.dumps(raw))


def test_foreign_definition_scope_rejected_before_registration():
    raw = request()
    raw["payload"]["definition"]["scope"]["project_id"] = "foreign"
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        parse_authoring_command("definition.save", json.dumps(raw))


def test_numeric_profile_is_explicit_and_limited_to_save_and_draft_admission():
    raw = request()
    raw["payload"]["definition"]["body"]["nodes"][0]["outputs"] = [
        {"port": "value", "source": {"kind": "number", "value": 1.25, "unit": "1"}}]
    with pytest.raises(CommandEncodingError, match="non_integer_number"):
        parse_authoring_command("definition.save", json.dumps(raw))
    raw["encoding"] = "amphora-command-v2"
    parsed = parse_authoring_command("definition.save", json.dumps(raw))
    assert parsed.profile == "amphora-command-v2"
    assert parse_authoring_command("definition.save", parsed.canonical_bytes) == parsed
    for family, payload, parser in [
        ("definition.validate", {"draft_id": "draft-1", "revision": 1, "content_sha256": "a" * 64}, parse_authoring_command),
        ("graph.advance", {"run_id": "run"}, parse_graph_command),
        ("graph.admit", {"plan_sha256": "a" * 64, "inputs": [], "budget": {"limit": 1}}, parse_graph_command),
    ]:
        envelope = {"encoding": "amphora-command-v2", "identity": {**raw["identity"], "command_family": family}, "payload": payload}
        with pytest.raises(CommandEncodingError, match="invalid_envelope"):
            parser(family, json.dumps(envelope))


def test_revision_response_preserves_scope_and_parent_identity():
    raw = {"scope": SCOPE, "head": {"draft_id": "draft-1", "revision": 2, "content_sha256": "a" * 64, "title": "Draft"},
        "parent_revision": 1, "definition": definition()}
    assert DraftRevision.model_validate_json(json.dumps(raw)).head.revision == 2
    raw["parent_revision"] = 0
    with pytest.raises(ValidationError, match="inconsistent_draft_identity"):
        DraftRevision.model_validate_json(json.dumps(raw))


def test_validation_is_revision_pinned_and_cannot_claim_scientific_acceptance():
    raw = {"scope": SCOPE, "validation_id": "validation-1", "draft_id": "draft-1", "revision": 1,
        "content_sha256": "a" * 64, "universe_sha256": "b" * 64, "structurally_valid": True,
        "plan_sha256": "c" * 64, "findings": [], "pending_checks": ["current_eligibility", "activation", "scientific_applicability"]}
    value = DraftValidation.model_validate_json(json.dumps(raw))
    assert value.scientific_acceptance == "not_established"
    for changes in ({"plan_sha256": None}, {"scientific_acceptance": "accepted"}, {"executable": True}):
        with pytest.raises(ValidationError):
            DraftValidation.model_validate_json(json.dumps({**raw, **changes}))


def test_authoring_receipt_does_not_reinterpret_runtime_execution_receipts():
    command = parse_authoring_command("definition.save", json.dumps(request()))
    raw = {"outcome": {"status": "accepted", "binding": {"identity": command.identity.model_dump(),
        "request_sha256": command.sha256, "operation_id": "operation-1"},
        "committed": {"kind": "draft_revision", "object_id": "draft-1", "revision": 1, "content_sha256": "a" * 64}}}
    value = DraftCommandReceipt.model_validate_json(json.dumps(raw))
    assert DraftCommandReceipt.model_validate_json(value.model_dump_json()) == value
    with pytest.raises(ValidationError):
        CommandReceipt.model_validate_json(json.dumps(raw))
