import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.extraction import TraceProjection
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import CapturedOutput, Observation, unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.publication import (
    AttemptIdentity,
    PublicationAttempt,
    PublicationIdentity,
    TraceArtifact,
    content_schema,
    content_schema_bytes,
)
from amphora_agent_planning.source_access import SourceReviewer
from amphora_contracts_artifacts import (
    DerivationReceipt,
    DerivedUploadReceipt,
    FinalizedReceipt,
    UploadContentReceipt,
    UploadReceipt,
)
from amphora_contracts_core import ArtifactRef
from amphora_contracts_planning import ExtractionTrace

from ..source_access.test_review import inputs


def prepared():
    task, data = inputs()
    review = SourceReviewer(data).review(task)
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    class Provider:
        def supports(self, model):
            return True
        def reply(self, binding):
            return ProviderReply((json.dumps(raw["draft"]).encode(),), unknown_usage())
    observed = observe(AttemptBinding(task.request, 1), Provider())
    assert observed.document().status == "proposed"
    projection = TraceProjection.derive("trace", task, observed)
    principal = Principal("fixture", task.document().scope, frozenset({"record_attempts"}))
    identity = PublicationIdentity.bind(principal, "publication", projection.reference(), "data-owner")
    artifact = TraceArtifact.reviewed(identity, projection, review)
    return identity, projection, review, artifact


def receipts(identity, artifact, attempt):
    upload = DerivedUploadReceipt(upload=UploadReceipt(upload_id="upload", scope=identity.trace().scope,
                                                       content=artifact.content), declaration=artifact.declaration)
    stream = UploadContentReceipt(upload_id="upload", attempt_id="stream", generation=1)
    ref = ArtifactRef(artifact_id="output", scope=identity.trace().scope, **artifact.content.model_dump())
    final = FinalizedReceipt(upload_id="upload", artifact=ref)
    command = attempt.begin_command(identity, artifact)
    derivation = DerivationReceipt(origin=command.identity, request_sha256=command.sha256, upload_id="upload",
                                   artifact=ref, declaration=artifact.declaration)
    return upload, stream, final, derivation


def test_exact_trace_content_separate_schema_and_full_derived_ancestry():
    identity, projection, review, artifact = prepared()
    assert artifact.body == projection.canonical
    assert artifact.content.sha256 == hashlib.sha256(artifact.body).hexdigest() == identity.trace().sha256
    assert artifact.content.schema_ref == content_schema()
    assert artifact.declaration.inputs == review.inputs()
    assert len(artifact.declaration.inputs) == 6
    assert json.loads(artifact.body)["authority"] == "interpretation_only"
    schema = json.loads(content_schema_bytes())
    assert "$id" not in schema and schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    expected = ExtractionTrace.model_json_schema(mode="validation")
    expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    assert schema == expected and len(content_schema_bytes()) < 65536
    assert TraceArtifact.reviewed(identity, projection, review) == artifact


@pytest.mark.parametrize("case,code", [("missing-input", "publication_input_missing"),
    ("duplicate-input", "publication_input_count"), ("missing-source", "publication_source_review"),
    ("missing-trace", "publication_trace_review"), ("foreign-input", "publication_input_scope")])
def test_fabricated_review_cannot_omit_consumed_ancestry(case, code):
    identity, projection, review, _ = prepared()
    if case == "missing-input":
        review = replace(review, artifact_documents=review.artifact_documents[1:])
    elif case == "duplicate-input":
        review = replace(review, artifact_documents=review.artifact_documents * 2)
    elif case == "missing-source":
        review = replace(review, source_documents=())
    elif case == "missing-trace":
        review = replace(review, trace_documents=())
    else:
        raw = json.loads(review.artifact_documents[0])
        raw["scope"]["project_id"] = "foreign"
        review = replace(review, artifact_documents=(json.dumps(raw).encode(), *review.artifact_documents[1:]))
    with pytest.raises(ValueError, match=code):
        TraceArtifact.reviewed(identity, projection, review)


def test_identity_requires_existing_writer_grant_and_exact_trace_actor():
    identity, projection, review, _ = prepared()
    principal = Principal("fixture", identity.trace().scope, frozenset())
    with pytest.raises(PermissionError):
        PublicationIdentity.bind(principal, "publication", identity.trace(), "data-owner")
    other = Principal("other", principal.scope, frozenset({"record_attempts"}))
    forged = PublicationIdentity.bind(other, "publication", identity.trace(), "data-owner")
    with pytest.raises(ValueError, match="publication_actor_binding"):
        TraceArtifact.reviewed(forged, projection, review)
    wrong = PublicationIdentity.bind(replace(other, actor_id="fixture"), "publication",
                                     identity.trace().model_copy(update={"sha256": "f" * 64}), "data-owner")
    with pytest.raises(ValueError, match="publication_trace_binding"):
        TraceArtifact.reviewed(wrong, projection, review)


def test_failed_interpretation_publishes_honest_diagnostics_not_a_candidate():
    identity, first, review, _ = prepared()
    binding = AttemptBinding(review.task.request, 2)
    observed = Observation.record(binding, CapturedOutput(b"partial", False), "unknown",
                                  "response_interrupted", unknown_usage())
    trace = TraceProjection.derive("failed", review.task, observed, first)
    principal = Principal(identity.actor_id, identity.trace().scope, frozenset({"record_attempts"}))
    identity = PublicationIdentity.bind(principal, "failed-publication", trace.reference(), "data-owner")
    artifact = TraceArtifact.reviewed(identity, trace, review)
    record = ExtractionTrace.model_validate_json(artifact.body)
    assert record.outcome.status == "unknown" and record.outcome.candidate_sha256 is None
    assert not record.fields and record.authority == "interpretation_only"
    assert record.prior == first.reference()


@pytest.mark.parametrize("field,value,code", [("task_id", "other", "publication_task_binding"),
    ("policy", None, "publication_trace_provenance")])
def test_published_trace_must_match_the_reviewed_task_and_context(field, value, code):
    identity, projection, review, _ = prepared()
    raw = projection.document().model_dump(mode="json")
    if field == "policy":
        raw[field]["artifact_id"] = "another-policy"
    else:
        raw[field] = value
    projection = TraceProjection(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode())
    principal = Principal(identity.actor_id, identity.trace().scope, frozenset({"record_attempts"}))
    identity = PublicationIdentity.bind(principal, "publication", projection.reference(), "data-owner")
    with pytest.raises(ValueError, match=code):
        TraceArtifact.reviewed(identity, projection, review)


def test_stable_commands_successful_transition_and_exact_derivation_binding():
    identity, _, _, artifact = prepared()
    first = PublicationAttempt.first(identity)
    assert first == PublicationAttempt.first(identity)
    assert first.identity.begin_id != first.identity.finalize_id
    upload, stream, final, derivation = receipts(identity, artifact, first)
    begun = first.begun(identity, artifact, upload)
    streaming = begun.start_stream()
    streamed = streaming.streamed(stream)
    finalizing = streamed.start_finalize()
    assert finalizing.finalize_command(identity).identity.command_id == first.identity.finalize_id
    result = finalizing.finalized(identity, artifact, final, derivation)
    assert result.stage == "finalized" and result.result == derivation
    assert first.stage == "prepared" and first.upload is None
    assert result.begin_command(identity, artifact).sha256 == first.begin_command(identity, artifact).sha256


def test_unknown_stream_is_retained_and_replaced_without_replaying_put():
    identity, _, _, artifact = prepared()
    first = PublicationAttempt.first(identity)
    upload, _, _, _ = receipts(identity, artifact, first)
    unknown = first.begun(identity, artifact, upload).start_stream().abandon()
    second = unknown.replacement(identity)
    assert unknown.stage == "abandoned" and unknown.upload == upload
    assert second.stage == "prepared" and second.identity.ordinal == 2
    assert second.identity.begin_id != first.identity.begin_id and second.identity.finalize_id != first.identity.finalize_id
    with pytest.raises(ValueError, match="publication_transition"):
        unknown.start_finalize()
    with pytest.raises(ValueError, match="publication_transition"):
        unknown.start_stream()


def test_ambiguous_finalization_cannot_be_abandoned_or_restreamed():
    identity, _, _, artifact = prepared()
    first = PublicationAttempt.first(identity)
    upload, stream, _, _ = receipts(identity, artifact, first)
    finalizing = first.begun(identity, artifact, upload).start_stream().streamed(stream).start_finalize()
    original = finalizing.finalize_command(identity)
    for operation in (finalizing.abandon, finalizing.start_stream, lambda: finalizing.replacement(identity)):
        with pytest.raises(ValueError, match="publication_transition"):
            operation()
    assert finalizing.finalize_command(identity) == original
    rejected = finalizing.rejected("rights_revoked")
    assert rejected.stage == "rejected" and rejected.rejection == "rights_revoked"


@pytest.mark.parametrize("ordinal", [0, 9, True])
def test_upload_replacements_remain_bounded(ordinal):
    identity, _, _, _ = prepared()
    with pytest.raises(ValueError, match="publication_attempt_limit"):
        AttemptIdentity.for_publication(identity, ordinal)


@pytest.mark.parametrize("case", ["upload", "stream", "final", "declaration", "origin", "digest"])
def test_peer_receipts_cannot_change_scope_payload_or_publication_origin(case):
    identity, _, _, artifact = prepared()
    first = PublicationAttempt.first(identity)
    upload, stream, final, derivation = receipts(identity, artifact, first)
    if case == "upload":
        upload = upload.model_copy(update={"declaration": upload.declaration.model_copy(update={
            "inputs": upload.declaration.inputs[1:]})})
    try:
        begun = first.begun(identity, artifact, upload).start_stream()
        if case == "stream":
            stream = stream.model_copy(update={"upload_id": "other"})
        finalizing = begun.streamed(stream).start_finalize()
        if case == "final":
            final = final.model_copy(update={"artifact": final.artifact.model_copy(update={"sha256": "f" * 64})})
        elif case == "declaration":
            derivation = derivation.model_copy(update={"declaration": derivation.declaration.model_copy(update={
                "inputs": derivation.declaration.inputs[1:]})})
        elif case == "origin":
            derivation = derivation.model_copy(update={"origin": derivation.origin.model_copy(update={"command_id": "other"})})
        elif case == "digest":
            derivation = derivation.model_copy(update={"request_sha256": "f" * 64})
        finalizing.finalized(identity, artifact, final, derivation)
    except ValueError as exc:
        assert str(exc) in {"publication_upload_binding", "publication_stream_binding", "publication_finalization_binding"}
    else:
        pytest.fail("Altered peer receipt must not advance publication")
