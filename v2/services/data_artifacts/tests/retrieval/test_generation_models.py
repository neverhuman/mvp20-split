"""Synthetic pure generation identities; no index, persistence or rights authority claim."""

from dataclasses import replace

import pytest
from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_evidence import SourceRevisionRef, SourceSpan
from amphora_data_artifacts.representations.bindings.document import VectorPublication
from amphora_data_artifacts.representations.bindings.identity import SourceBindingIdentity
from amphora_data_artifacts.representations.bindings.receipts import BindingReceipts
from amphora_data_artifacts.representations.fixture import FixtureEncoder, fixture_profile
from amphora_data_artifacts.representations.identity import EncodingInput
from amphora_data_artifacts.representations.mapping import profile_reference
from amphora_data_artifacts.representations.payloads import EncodedRepresentation
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.retrieval.identity import BuildAttempt, GenerationPlan, GenerationReference
from amphora_data_artifacts.retrieval.lifecycle import GenerationPhase
from amphora_data_artifacts.retrieval.manifest import CorpusManifest
from amphora_data_artifacts.retrieval.validation import RetrievalError, canonical

SCOPE = Scope(tenant_id="fixture", project_id="generation")
PROFILE = fixture_profile()
BACKEND = SchemaRef(schema_id="fixture.projection-protocol", version="1", sha256="a" * 64)


def binding(index, *, scope=SCOPE, profile=PROFILE):
    source = EncodingInput(b"ABBA")
    raw = ArtifactRef(
        scope=scope,
        artifact_id="raw-" + str(index),
        sha256=source.sha256,
        size_bytes=4,
        media_type="application/octet-stream",
        schema_ref=profile.encoder.implementation,
    )
    span = SourceSpan(
        source=SourceRevisionRef(scope=scope, source_id="source-" + str(index), revision_id="r1", raw=raw),
        unit="byte",
        start=0,
        end=4,
        sha256=source.sha256,
    )
    identity = SourceBindingIdentity(scope, "publisher", profile_reference(scope, profile), span)
    publication = VectorPublication(
        identity, EncodedRepresentation.prepare(profile, source, FixtureEncoder().encode(profile, source))
    )
    command = publication.command("begin")
    artifact = ArtifactRef(
        scope=scope, artifact_id="vector-" + str(index), **publication.content.model_dump()
    )
    receipt = DerivationReceipt(
        origin=command.identity,
        request_sha256=command.sha256,
        upload_id="upload-" + str(index),
        artifact=artifact,
        declaration=publication.declaration,
    )
    return BindingReceipts(publication).finalized(receipt.upload_id, receipt)


def test_manifest_order_complete_binding_and_point_identity_are_stable():
    first, second = binding(1), binding(2)
    manifest = CorpusManifest(SCOPE, PROFILE, (first, second))
    same = CorpusManifest(SCOPE, PROFILE, (first, second))
    reverse = CorpusManifest(SCOPE, PROFILE, (second, first))
    assert manifest.watermark == same.watermark
    assert reverse.watermark != manifest.watermark
    assert reverse.point_ids == tuple(reversed(manifest.point_ids))
    assert len(set(manifest.point_ids)) == 2
    with pytest.raises(RetrievalError, match="duplicate_binding"):
        CorpusManifest(SCOPE, PROFILE, (first, first))
    forged = first.model_copy(update={"reference": first.reference.model_copy(update={"sha256": "0" * 64})})
    with pytest.raises(RepresentationError, match="binding_conflict"):
        CorpusManifest(SCOPE, PROFILE, (forged,))


def test_manifest_rejects_cross_scope_profile_and_unconfigured_pairing():
    with pytest.raises(RepresentationError, match="binding_scope"):
        CorpusManifest(SCOPE, PROFILE, (binding(1, scope=SCOPE.model_copy(update={"project_id": "other"})),))
    with pytest.raises(RetrievalError, match="binding_profile"):
        CorpusManifest(SCOPE, PROFILE, (binding(1, profile=fixture_profile("l2")),))
    document = replace(PROFILE, inputs=replace(PROFILE.inputs, role="document"))
    with pytest.raises(RepresentationError, match="pairing_unconfigured"):
        CorpusManifest(SCOPE, document, (binding(1),))


def test_full_bound_manifest_exceeds_command_limit_without_truncating():
    bindings = tuple(binding(i) for i in range(256))
    manifest = CorpusManifest(SCOPE, PROFILE, bindings)
    assert len(canonical(manifest.descriptor())) > 65536
    assert len(manifest.point_ids) == 256
    for invalid in ((), bindings + (binding(256),), list(bindings)):
        with pytest.raises(RetrievalError, match="corpus_bound"):
            CorpusManifest(SCOPE, PROFILE, invalid)
    with pytest.raises(RetrievalError, match="manifest_bound"):
        canonical({"oversized": "x" * (4 * 1024 * 1024)})


def test_point_collision_fails_before_projection_can_overwrite(monkeypatch):
    import amphora_data_artifacts.retrieval.manifest as module

    monkeypatch.setattr(module, "point_id", lambda binding: "collision")
    with pytest.raises(RetrievalError, match="point_collision"):
        CorpusManifest(SCOPE, PROFILE, (binding(1), binding(2)))


def test_generation_pins_owner_manifest_expected_head_and_backend():
    manifest = CorpusManifest(SCOPE, PROFILE, (binding(1),))
    plan = GenerationPlan("corpus", "g1", "builder", manifest, None, BACKEND)
    assert plan.reference == replace(plan).reference
    head = GenerationReference(SCOPE, "corpus", "g0", "b" * 64)
    changes = (
        replace(plan, actor_id="other"),
        replace(plan, corpus_id="other"),
        replace(plan, generation_id="g2"),
        replace(plan, expected_head=head),
        replace(plan, backend_profile=BACKEND.model_copy(update={"sha256": "c" * 64})),
        replace(plan, manifest=CorpusManifest(SCOPE, PROFILE, (binding(2),))),
    )
    assert len({plan.reference.sha256, *(change.reference.sha256 for change in changes)}) == 7
    for ref, code in (
        (replace(head, corpus_id="other"), "head_scope"),
        (replace(head, scope=SCOPE.model_copy(update={"project_id": "other"})), "head_scope"),
        (replace(head, generation_id="g1"), "self_head"),
    ):
        with pytest.raises(RetrievalError, match=code):
            replace(plan, expected_head=ref)


def test_attempt_namespaces_isolate_stale_and_successor_builders():
    plan = GenerationPlan(
        "corpus", "g1", "builder", CorpusManifest(SCOPE, PROFILE, (binding(1),)), None, BACKEND
    )
    attempt = BuildAttempt(plan.reference, "token-one", 1)
    assert attempt.namespace == replace(attempt).namespace
    alternatives = (
        replace(attempt, token="token-two"),
        replace(attempt, fence=2),
        replace(attempt, generation=replace(plan, generation_id="g2").reference),
    )
    assert len({attempt.namespace, *(item.namespace for item in alternatives)}) == 4
    for fence in (True, 0, 9007199254740992):
        with pytest.raises(RetrievalError, match="fence_bound"):
            replace(attempt, fence=fence)


def test_transition_policy_forbids_skips_and_terminal_reopening():
    allowed = {
        ("prepared", "building"),
        ("prepared", "abandoned"),
        ("building", "verified"),
        ("building", "failed"),
        ("building", "abandoned"),
        ("verified", "published"),
        ("verified", "failed"),
        ("verified", "abandoned"),
    }
    for source in GenerationPhase:
        for target in GenerationPhase:
            if (source.value, target.value) in allowed:
                assert source.require_successor(target) is target
            else:
                with pytest.raises(RetrievalError, match="phase_transition"):
                    source.require_successor(target)
    with pytest.raises(RetrievalError, match="phase_required"):
        GenerationPhase.PREPARED.require_successor("building")


def test_generation_wire_roundtrip_and_status_are_explicit_projections():
    from amphora_data_artifacts.retrieval.mapping import (
        plan_from_wire,
        plan_to_wire,
        reference_from_wire,
        reference_to_wire,
        status_to_wire,
    )

    old = GenerationReference(SCOPE, "corpus", "old", "b" * 64)
    for head in (None, old):
        plan = GenerationPlan("corpus", "new", "owner", CorpusManifest(SCOPE, PROFILE, (binding(1),)), head, BACKEND)
        wire = plan_to_wire(plan)
        assert plan_from_wire(PROFILE, wire) == plan
        assert reference_from_wire(reference_to_wire(plan.reference)) == plan.reference
        for phase in GenerationPhase:
            status = status_to_wire(plan, phase)
            assert status.state == phase.value
            assert status.generation == wire
    with pytest.raises(RetrievalError, match="phase_required"):
        status_to_wire(plan, "published")


def test_mapping_rejects_shape_bypasses_and_recomputed_identity_mismatches():
    from amphora_data_artifacts.retrieval.mapping import manifest_from_wire, plan_from_wire, plan_to_wire

    plan = GenerationPlan("corpus", "new", "owner", CorpusManifest(SCOPE, PROFILE, (binding(1),)), None, BACKEND)
    wire = plan_to_wire(plan)
    for forged in (
        wire.model_copy(update={"actor_id": "another"}),
        wire.model_copy(update={"backend_profile": BACKEND.model_copy(update={"sha256": "d" * 64})}),
        wire.model_copy(update={"reference": wire.reference.model_copy(update={"scope": Scope(tenant_id="other", project_id="other")})}),
    ):
        with pytest.raises(RetrievalError, match="generation_digest"):
            plan_from_wire(PROFILE, forged)
    with pytest.raises(RetrievalError, match="manifest_watermark"):
        manifest_from_wire(PROFILE, wire.manifest.model_copy(update={"watermark": "0" * 64}))
    with pytest.raises(RetrievalError, match="manifest_profile"):
        manifest_from_wire(PROFILE, wire.manifest.model_copy(update={"profile": wire.manifest.profile.model_copy(update={"version": "2"})}))
    with pytest.raises(RepresentationError, match="wire_shape"):
        plan_from_wire(PROFILE, wire.model_copy(update={"actor_id": False}))


def test_generation_request_binds_exact_order_owner_actor_and_backend():
    from amphora_contracts_representations import BuildIndexGeneration
    from amphora_data_artifacts.retrieval.mapping import plan_from_request, reference_to_wire

    bindings = (binding(1), binding(2))
    request = BuildIndexGeneration(wire_version="1", corpus_id="corpus", generation_id="new",
        profile=bindings[0].profile, bindings=tuple(b.reference for b in bindings), expected_head=None)
    result = plan_from_request(SCOPE, "owner", request, PROFILE, bindings, BACKEND)
    assert result.actor_id == "owner"
    assert result.backend_profile == BACKEND
    assert result.manifest.bindings == bindings
    old = GenerationReference(SCOPE, "corpus", "old", "c" * 64)
    request_with_head = request.model_copy(update={"expected_head": reference_to_wire(old)})
    assert plan_from_request(SCOPE, "owner", request_with_head, PROFILE, bindings, BACKEND).expected_head == old
    with pytest.raises(RetrievalError, match="request_bindings"):
        plan_from_request(SCOPE, "owner", request, PROFILE, tuple(reversed(bindings)), BACKEND)
    with pytest.raises(RetrievalError, match="request_profile"):
        plan_from_request(SCOPE, "owner", request.model_copy(update={"profile": request.profile.model_copy(update={"version": "2"})}), PROFILE, bindings, BACKEND)
