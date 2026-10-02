import json
from dataclasses import replace

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_commands import CanonicalCommand
from amphora_contracts_core import ArtifactRef, Scope
from amphora_data_artifacts.derivations.model import DeclaredTransformation
from amphora_data_artifacts.publication.model import Principal, UploadError


@pytest.fixture
def declaration():
    principal = Principal("producer", Scope(tenant_id="internal", project_id="demo"), frozenset({"read", "upload"}))
    content = {"sha256": "a" * 64, "size_bytes": 10, "media_type": "text/plain",
               "schema_ref": {"schema_id": "text", "version": "1", "sha256": "b" * 64}}
    artifact = {**content, "artifact_id": "input-1", "scope": principal.scope.model_dump()}
    raw = {"identity": {"actor_id": principal.actor_id, "scope": principal.scope.model_dump(),
                         "command_family": "artifacts.begin_derived_upload", "command_id": "begin-1"},
           "payload": {"content": content, "declaration": {
               "transformation": {"transformation_id": "transform", "version": "1", "sha256": "c" * 64},
               "inputs": [artifact]}}}
    return principal, raw


def parsed(raw):
    return parse_command("artifacts.begin_derived_upload", json.dumps(raw))


def test_exact_output_and_original_input_identity(declaration):
    principal, raw = declaration
    model = DeclaredTransformation.authorized(principal, parsed(raw))
    output = ArtifactRef.model_validate_json(json.dumps({**raw["payload"]["declaration"]["inputs"][0], "artifact_id": "output-1"}))
    receipt = model.receipt("upload-1", output)
    assert model.input_ids == ("input-1",)
    assert receipt.origin == model.command.identity
    assert receipt.request_sha256 == model.command.sha256
    assert receipt.declaration == model.request.declaration
    with pytest.raises(UploadError, match="derivation_output_mismatch"):
        model.receipt("upload-1", output.model_copy(update={"sha256": "d" * 64}))
    with pytest.raises(UploadError, match="derivation_scope_mismatch"):
        model.receipt("upload-1", output.model_copy(update={"scope": Scope(tenant_id="foreign", project_id="demo")}))


@pytest.mark.parametrize("conflicting", [False, True])
def test_repeated_input_id_is_not_two_sources(declaration, conflicting):
    principal, raw = declaration
    inputs = raw["payload"]["declaration"]["inputs"]
    inputs.append({**inputs[0], **({"sha256": "d" * 64} if conflicting else {})})
    with pytest.raises(UploadError, match="derivation_duplicate_input"):
        DeclaredTransformation.authorized(principal, parsed(raw))


@pytest.mark.parametrize("actions", [frozenset({"upload"}), frozenset({"read"})])
def test_processing_requires_upload_and_read_privileges(declaration, actions):
    principal, raw = declaration
    with pytest.raises(UploadError, match="access_denied"):
        DeclaredTransformation.authorized(replace(principal, actions=actions), parsed(raw))


def test_constructed_command_cannot_substitute_authenticated_identity(declaration):
    principal, raw = declaration
    command = parsed(raw)
    raw["identity"]["actor_id"] = "other"
    forged = CanonicalCommand(command.identity, parsed(raw).canonical_bytes)
    with pytest.raises(UploadError, match="derivation_command_mismatch"):
        DeclaredTransformation.authorized(principal, forged)


def test_input_order_is_bound_to_command_identity(declaration):
    principal, raw = declaration
    inputs = raw["payload"]["declaration"]["inputs"]
    inputs.append({**inputs[0], "artifact_id": "input-2"})
    first = DeclaredTransformation.authorized(principal, parsed(raw))
    inputs.reverse()
    second = DeclaredTransformation.authorized(principal, parsed(raw))
    assert first.command.sha256 != second.command.sha256
    assert second.input_ids == ("input-2", "input-1")
