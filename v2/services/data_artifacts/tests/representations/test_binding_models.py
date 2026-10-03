"""Source attribution and actual public command/receipt shapes, with no I/O claim."""

import hashlib
import json
from dataclasses import replace

import pytest
from amphora_contracts_artifacts import (
    DerivationReceipt,
    DerivedUploadAccepted,
    DerivedUploadObservation,
    DerivedUploadReceipt,
    PublicationPending,
    UploadReceipt,
)
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_evidence import SourceRevisionRef, SourceSpan
from amphora_contracts_representations import EncodeSourceRequest
from amphora_data_artifacts.publication.model import Principal
from amphora_data_artifacts.representations.bindings.content_rule import VectorContentRule
from amphora_data_artifacts.representations.bindings.document import VectorPublication
from amphora_data_artifacts.representations.bindings.identity import SourceBindingIdentity
from amphora_data_artifacts.representations.bindings.receipts import BindingReceipts
from amphora_data_artifacts.representations.fixture import FixtureEncoder, fixture_profile
from amphora_data_artifacts.representations.identity import EncodingInput
from amphora_data_artifacts.representations.mapping import profile_reference, vector_to_wire
from amphora_data_artifacts.representations.payloads import EncodedRepresentation
from amphora_data_artifacts.representations.validation import RepresentationError


@pytest.fixture
def publication():
    scope = Scope(tenant_id="fixture", project_id="bindings")
    principal = Principal("publisher", scope, frozenset())
    profile = fixture_profile()
    source = EncodingInput(b"ABBA")
    raw = ArtifactRef(
        artifact_id="source-artifact",
        scope=scope,
        sha256=source.sha256,
        size_bytes=4,
        media_type="application/octet-stream",
        schema_ref=profile.encoder.implementation,
    )
    span = SourceSpan(
        source=SourceRevisionRef(scope=scope, source_id="source", revision_id="r1", raw=raw),
        unit="byte",
        start=0,
        end=4,
        sha256=source.sha256,
    )
    request = EncodeSourceRequest(
        wire_version="1", encoding_id="first", profile=profile_reference(scope, profile), source=span
    )
    identity = SourceBindingIdentity.prepare(principal, request)
    encoded = EncodedRepresentation.prepare(profile, source, FixtureEncoder().encode(profile, source))
    return principal, request, VectorPublication(identity, encoded)


def receipts(pub):
    command = pub.command("begin")
    upload = UploadReceipt(upload_id="upload", scope=pub.identity.scope, content=pub.content)
    observation = DerivedUploadObservation(
        identity=command.identity,
        operation_id="operation",
        request_sha256=command.sha256,
        outcome=DerivedUploadAccepted(
            receipt=DerivedUploadReceipt(upload=upload, declaration=pub.declaration)
        ),
    )
    artifact = ArtifactRef(artifact_id="vector", scope=pub.identity.scope, **pub.content.model_dump())
    final = DerivationReceipt(
        origin=command.identity,
        request_sha256=command.sha256,
        upload_id="upload",
        artifact=artifact,
        declaration=pub.declaration,
    )
    return observation, final


def test_aliases_converge_but_source_actor_profile_and_span_remain_distinct(publication):
    principal, request, pub = publication
    alias = request.model_copy(update={"encoding_id": "another-workflow"})
    assert SourceBindingIdentity.prepare(principal, alias) == pub.identity
    assert pub.command("begin") == replace(
        pub, identity=SourceBindingIdentity.prepare(principal, alias)
    ).command("begin")
    other_source = request.source.model_copy(
        update={"source": request.source.source.model_copy(update={"source_id": "other"})}
    )
    changes = [
        replace(pub.identity, actor_id="other"),
        replace(pub.identity, source=other_source),
        replace(pub.identity, profile=request.profile.model_copy(update={"sha256": "a" * 64})),
        replace(pub.identity, source=request.source.model_copy(update={"start": 1})),
    ]
    assert all(x.binding_id != pub.identity.binding_id for x in changes)
    assert (
        len({pub.command("begin").identity.command_id, pub.command("finalize", "upload").identity.command_id})
        == 2
    )
    assert len(pub.command("finalize", "upload").identity.command_id) <= 128


def test_payload_and_final_binding_preserve_exact_single_source(publication):
    _, request, pub = publication
    assert pub.declaration.inputs == (request.source.source.raw,)
    assert pub.content.sha256 == hashlib.sha256(pub.payload).hexdigest()
    assert json.loads(pub.payload) == json.loads(
        vector_to_wire(pub.identity.scope, pub.encoded).model_dump_json()
    )
    observation, final = receipts(pub)
    verifier = BindingReceipts(pub)
    assert verifier.upload(observation) == "upload"
    binding = verifier.finalized("upload", final)
    assert binding.reference.binding_id == pub.identity.binding_id and binding.source == request.source
    assert binding.vector == final.artifact and binding.profile == request.profile
    assert verifier.finalized("upload", final) == binding
    changed = final.model_copy(
        update={"artifact": final.artifact.model_copy(update={"artifact_id": "different"})}
    )
    assert verifier.finalized("upload", changed).reference.sha256 != binding.reference.sha256
    with pytest.raises(RepresentationError, match="self_derivation"):
        verifier.finalized(
            "upload",
            final.model_copy(
                update={
                    "artifact": final.artifact.model_copy(
                        update={"artifact_id": request.source.source.raw.artifact_id}
                    )
                }
            ),
        )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"start": 4}, "span_bound"),
        ({"end": 5}, "span_bound"),
        ({"end": 0}, "span_bound"),
    ],
)
def test_invalid_span_fails_before_source_loading(publication, change, reason):
    _, request, pub = publication
    with pytest.raises(RepresentationError, match=reason):
        replace(pub.identity, source=request.source.model_copy(update=change))


def test_scope_forgery_size_input_and_stage_mismatches_fail(publication):
    _, request, pub = publication
    other = Scope(tenant_id="other", project_id="other")
    with pytest.raises(RepresentationError, match="binding_scope"):
        replace(pub.identity, scope=other)
    huge = request.source.model_copy(
        update={
            "source": request.source.source.model_copy(
                update={"raw": request.source.source.raw.model_copy(update={"size_bytes": 4194305})}
            )
        }
    )
    with pytest.raises(RepresentationError, match="source_bound"):
        replace(pub.identity, source=huge)
    with pytest.raises(RepresentationError, match="binding_profile"):
        replace(
            pub,
            identity=replace(pub.identity, profile=request.profile.model_copy(update={"sha256": "a" * 64})),
        )
    with pytest.raises(RepresentationError, match="binding_input"):
        replace(pub, encoded=replace(pub.encoded, input_sha256="a" * 64))
    with pytest.raises(RepresentationError, match="binding_required"):
        VectorPublication(None, pub.encoded)
    with pytest.raises(RepresentationError, match="encoded_required"):
        VectorPublication(pub.identity, None)
    with pytest.raises(RepresentationError, match="publication_required"):
        BindingReceipts(None)
    for stage, upload, reason in [
        ("unknown", None, "publication_stage"),
        ("begin", "upload", "upload_identity"),
        ("finalize", None, "upload_identity"),
    ]:
        with pytest.raises(RepresentationError, match=reason):
            pub.command(stage, upload)


def test_wrong_upload_origin_content_and_lineage_cannot_publish_binding(publication):
    _, _, pub = publication
    observation, final = receipts(pub)
    verifier = BindingReceipts(pub)
    for change, reason in [
        ({"request_sha256": "a" * 64}, "upload_identity"),
        ({"outcome": PublicationPending()}, "upload_pending"),
    ]:
        with pytest.raises(RepresentationError, match=reason):
            verifier.upload(observation.model_copy(update=change))
    uploaded = observation.outcome.receipt
    bad_content = uploaded.upload.content.model_copy(update={"sha256": "a" * 64})
    bad_upload = uploaded.model_copy(
        update={"upload": uploaded.upload.model_copy(update={"content": bad_content})}
    )
    with pytest.raises(RepresentationError, match="upload_receipt"):
        verifier.upload(observation.model_copy(update={"outcome": DerivedUploadAccepted(receipt=bad_upload)}))
    bad_declaration = pub.declaration.model_copy(
        update={"inputs": (pub.declaration.inputs[0], pub.declaration.inputs[0])}
    )
    with pytest.raises(RepresentationError, match="derivation_receipt"):
        verifier.upload(
            observation.model_copy(
                update={
                    "outcome": DerivedUploadAccepted(
                        receipt=uploaded.model_copy(update={"declaration": bad_declaration})
                    )
                }
            )
        )
    for change, reason in [
        ({"upload_id": "other"}, "derivation_identity"),
        ({"request_sha256": "a" * 64}, "derivation_identity"),
        ({"declaration": bad_declaration}, "derivation_receipt"),
        ({"artifact": final.artifact.model_copy(update={"sha256": "a" * 64})}, "vector_artifact"),
    ]:
        with pytest.raises(RepresentationError, match=reason):
            verifier.finalized("upload", final.model_copy(update=change))


def test_vector_content_rule_checks_canonical_binary_bytes_not_just_json_shape(publication):
    _, _, pub = publication
    rule = VectorContentRule()
    assert rule.identity == (
        "application/json",
        pub.content.schema_ref.schema_id,
        "1",
        pub.content.schema_ref.sha256,
    )
    value = json.loads(pub.payload)
    rule.validate(value)
    for updates, reason in [
        ({"payload_sha256": "a" * 64}, "vector_digest"),
        ({"payload_hex": "00000000"}, "vector_length"),
        ({"payload_hex": "0000807f" + "00000000" * 15}, "vector_nonfinite"),
        ({"payload_hex": "00000080" + "00000000" * 15}, "vector_negative_zero"),
    ]:
        with pytest.raises(RepresentationError, match=reason):
            rule.validate(value | updates)


def test_numbered_retry_preserves_first_command_and_rejects_prior_receipts(publication):
    _, _, pub = publication
    first = pub.command("begin")
    assert pub.command("begin", attempt=1).canonical_bytes == first.canonical_bytes
    second = pub.command("begin", attempt=2)
    assert second.identity.command_id == first.identity.command_id + ".a2"
    assert second.sha256 != first.sha256
    observation, final = receipts(pub)
    checker = BindingReceipts(pub, 2)
    with pytest.raises(RepresentationError, match="upload_identity"):
        checker.upload(observation)
    with pytest.raises(RepresentationError, match="derivation_identity"):
        checker.finalized("upload", final)
    observation = observation.model_copy(
        update={"identity": second.identity, "request_sha256": second.sha256}
    )
    final = final.model_copy(update={"origin": second.identity, "request_sha256": second.sha256})
    assert checker.upload(observation) == "upload"
    assert checker.finalized("upload", final).reference.binding_id == pub.identity.binding_id
    for attempt in (0, -1, True, 1.0, 9007199254740992):
        with pytest.raises(RepresentationError, match="publication_attempt"):
            BindingReceipts(pub, attempt)
