from dataclasses import replace

import pytest
from amphora_contracts_artifacts import (
    BeginDerivedUpload,
    DerivationReceipt,
    DerivedUploadReceipt,
    FinalizeArtifact,
    FinalizedReceipt,
    UploadContentReceipt,
    UploadReceipt,
)
from amphora_contracts_core import ArtifactRef
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.publication.attempt import PublicationAttempt
from amphora_knowledge.publication.identity import PublisherIdentity
from amphora_knowledge.publication.payload import PublicationRequestDocument, ReasoningArtifact
from amphora_tool_protocol import WorkerIdentity
from pydantic import ValidationError


@pytest.fixture
def attempt_case(payload_case):
    principal, request, status, observed = payload_case
    artifact = ReasoningArtifact.reviewed(PublicationRequestDocument.authorized(principal, request), status, observed)
    publisher = PublisherIdentity("publisher", "issuer")
    attempt = PublicationAttempt.first()
    upload = DerivedUploadReceipt(upload=UploadReceipt(upload_id="upload-1", scope=request.graph.scope,
        content=artifact.content), declaration=artifact.declaration)
    stream = UploadContentReceipt(upload_id="upload-1", attempt_id="stream-1", generation=1)
    return artifact, publisher, attempt, upload, stream


def finalizing(case):
    artifact, _, attempt, upload, stream = case
    return attempt.accepted_upload(artifact, upload).start_stream().streamed(stream).start_finalize()


def final_receipts(case):
    artifact, publisher, attempt, upload, _ = case
    ref = ArtifactRef(artifact_id="output", scope=upload.upload.scope, **artifact.content.model_dump())
    receipt = FinalizedReceipt(upload_id=upload.upload.upload_id, artifact=ref)
    command = attempt.begin_command(artifact, publisher)
    derivation = DerivationReceipt(origin=command.identity, request_sha256=command.sha256, upload_id=receipt.upload_id,
        artifact=ref, declaration=artifact.declaration)
    return receipt, derivation


def test_verified_path_keeps_original_command_identities(attempt_case):
    artifact, publisher, original, _, _ = attempt_case
    active = finalizing(attempt_case)
    assert active.identity == original.identity
    receipt, derivation = final_receipts(attempt_case)
    finished = active.finalized(artifact, publisher, receipt, derivation)
    assert finished.stage == "finalized" and finished.result == derivation
    command = active.finalize_command(publisher)
    assert command == active.finalize_command(publisher)
    assert command.identity.command_id == original.identity.finalize_id


def test_commands_match_public_sdk_encoder_exactly(attempt_case):
    artifact, publisher, original, upload, _ = attempt_case
    begin = original.begin_command(artifact, publisher)
    identity = WorkerIdentity(publisher.actor_id, upload.upload.scope)
    assert identity.command("artifacts.begin_derived_upload", original.identity.begin_id,
        BeginDerivedUpload(content=artifact.content, declaration=artifact.declaration)).canonical_bytes == begin.canonical_bytes
    finalize = finalizing(attempt_case).finalize_command(publisher)
    assert identity.command("artifacts.finalize", original.identity.finalize_id,
        FinalizeArtifact(upload_id=upload.upload.upload_id, content=artifact.content)).canonical_bytes == finalize.canonical_bytes


def test_uncertain_stream_requires_explicit_bounded_replacement(attempt_case):
    artifact, _, attempt, upload, _ = attempt_case
    seen = set()
    for ordinal in range(1, 9):
        assert attempt.identity.ordinal == ordinal
        seen.update((attempt.identity.begin_id, attempt.identity.finalize_id))
        ambiguous = attempt.accepted_upload(artifact, upload).start_stream()
        with pytest.raises(KnowledgeError, match="publication_attempt_transition_invalid"):
            ambiguous.start_finalize()
        abandoned = ambiguous.abandon_stream()
        assert abandoned.upload == upload and abandoned.stream is None
        with pytest.raises(KnowledgeError, match="publication_attempt_transition_invalid"):
            abandoned.start_stream()
        if ordinal < 8:
            attempt = abandoned.replacement()
        else:
            with pytest.raises(KnowledgeError, match="publication_attempt_limit"):
                abandoned.replacement()
    assert len(seen) == 16


@pytest.mark.parametrize("stage", ["prepared", "begun", "streaming", "streamed", "finalizing", "finalized"])
def test_only_abandoned_stream_can_get_new_identity(attempt_case, stage):
    _, _, attempt, _, _ = attempt_case
    with pytest.raises(KnowledgeError, match="publication_attempt_transition_invalid"):
        replace(attempt, stage=stage).replacement()


def test_uncertain_finalization_cannot_be_abandoned_or_restreamed(attempt_case):
    _, _, _, _, stream = attempt_case
    attempt = finalizing(attempt_case)
    for operation in (attempt.abandon_stream, attempt.start_stream, lambda: attempt.streamed(stream)):
        with pytest.raises(KnowledgeError, match="publication_attempt_transition_invalid"):
            operation()


def test_payload_cannot_change_between_begin_and_finalize(attempt_case):
    artifact, publisher, original, upload, stream = attempt_case
    changed = replace(artifact, content=artifact.content.model_copy(update={"sha256": "0" * 64}))
    receipt, derivation = final_receipts((changed, publisher, original, upload, stream))
    with pytest.raises(KnowledgeError, match="publication_finalization_mismatch"):
        finalizing(attempt_case).finalized(changed, publisher, receipt, derivation)


@pytest.mark.parametrize("field", ["content", "scope", "declaration"])
def test_upload_substitution_is_rejected(attempt_case, field):
    artifact, _, attempt, receipt, _ = attempt_case
    if field == "declaration":
        receipt = receipt.model_copy(update={"declaration": receipt.declaration.model_copy(update={
            "transformation": receipt.declaration.transformation.model_copy(update={"version": "other"})})})
    else:
        upload = receipt.upload
        value = upload.content.model_copy(update={"sha256": "0" * 64}) if field == "content" else upload.scope.model_copy(update={"project_id": "other"})
        receipt = receipt.model_copy(update={"upload": upload.model_copy(update={field: value})})
    with pytest.raises(KnowledgeError, match="publication_upload_mismatch"):
        attempt.accepted_upload(artifact, receipt)


def test_wrong_stream_and_constructed_boolean_generation_are_rejected(attempt_case):
    artifact, _, attempt, upload, stream = attempt_case
    attempt = attempt.accepted_upload(artifact, upload).start_stream()
    with pytest.raises(KnowledgeError, match="publication_stream_mismatch"):
        attempt.streamed(stream.model_copy(update={"upload_id": "other"}))
    with pytest.raises(ValidationError):
        attempt.streamed(stream.model_copy(update={"generation": True}))


@pytest.mark.parametrize("variant", ["output_digest", "upload", "origin_actor", "origin_id", "command_hash", "declaration", "derivation_output"])
def test_finalized_metadata_must_bind_original_upload_and_exact_result(attempt_case, variant):
    artifact, publisher, _, _, _ = attempt_case
    receipt, derivation = final_receipts(attempt_case)
    if variant == "output_digest":
        receipt = receipt.model_copy(update={"artifact": receipt.artifact.model_copy(update={"sha256": "0" * 64})})
    elif variant == "upload":
        receipt = receipt.model_copy(update={"upload_id": "other"})
    elif variant.startswith("origin_"):
        field = "actor_id" if variant == "origin_actor" else "command_id"
        derivation = derivation.model_copy(update={"origin": derivation.origin.model_copy(update={field: "other"})})
    elif variant == "command_hash":
        derivation = derivation.model_copy(update={"request_sha256": "0" * 64})
    elif variant == "declaration":
        derivation = derivation.model_copy(update={"declaration": derivation.declaration.model_copy(update={
            "transformation": derivation.declaration.transformation.model_copy(update={"version": "other"})})})
    else:
        derivation = derivation.model_copy(update={"artifact": derivation.artifact.model_copy(update={"artifact_id": "other"})})
    with pytest.raises(KnowledgeError, match="publication_finalization_mismatch"):
        finalizing(attempt_case).finalized(artifact, publisher, receipt, derivation)
