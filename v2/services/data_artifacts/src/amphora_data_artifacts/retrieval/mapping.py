"""Explicit generation mapping; caller-provided DTOs never establish retained authority."""

from amphora_contracts_representations import (
    BuildIndexGeneration,
    IndexGeneration,
    IndexGenerationRef,
    IndexGenerationStatus,
    IndexManifest,
)

from ..representations.mapping import _validated
from .identity import GenerationPlan, GenerationReference
from .lifecycle import GenerationPhase
from .manifest import CorpusManifest
from .validation import require


def reference_to_wire(value):
    require(type(value) is GenerationReference, "retrieval_generation_required")
    return IndexGenerationRef.model_validate(value.descriptor())


def reference_from_wire(value):
    value = _validated(value, IndexGenerationRef)
    return GenerationReference(value.scope, value.corpus_id, value.generation_id, value.sha256)


def manifest_to_wire(value):
    require(type(value) is CorpusManifest, "retrieval_manifest_required")
    return IndexManifest(
        wire_version="1", scope=value.scope, profile=value.profile_reference,
        bindings=value.bindings, watermark=value.watermark,
    )


def manifest_from_wire(profile, value):
    value = _validated(value, IndexManifest)
    result = CorpusManifest(value.scope, profile, value.bindings)
    require(value.profile == result.profile_reference, "retrieval_manifest_profile")
    require(value.watermark == result.watermark, "retrieval_manifest_watermark")
    return result


def plan_to_wire(value):
    require(type(value) is GenerationPlan, "retrieval_plan_required")
    return IndexGeneration(
        wire_version="1", reference=reference_to_wire(value.reference), actor_id=value.actor_id,
        manifest=manifest_to_wire(value.manifest),
        expected_head=None if value.expected_head is None else reference_to_wire(value.expected_head),
        backend_profile=value.backend_profile,
    )


def plan_from_wire(profile, value):
    value = _validated(value, IndexGeneration)
    result = GenerationPlan(
        value.reference.corpus_id, value.reference.generation_id, value.actor_id,
        manifest_from_wire(profile, value.manifest),
        None if value.expected_head is None else reference_from_wire(value.expected_head),
        value.backend_profile,
    )
    require(reference_to_wire(result.reference) == value.reference, "retrieval_generation_digest")
    return result


def plan_from_request(scope, actor_id, request, profile, bindings, backend_profile):
    """Bindings/profile/backend are owner-selected inputs, not asserted request payloads."""
    request = _validated(request, BuildIndexGeneration)
    manifest = CorpusManifest(scope, profile, bindings)
    require(request.profile == manifest.profile_reference, "retrieval_request_profile")
    require(request.bindings == tuple(b.reference for b in bindings), "retrieval_request_bindings")
    return GenerationPlan(
        request.corpus_id, request.generation_id, actor_id, manifest,
        None if request.expected_head is None else reference_from_wire(request.expected_head),
        backend_profile,
    )


def status_to_wire(plan, phase):
    require(type(phase) is GenerationPhase, "retrieval_phase_required")
    return IndexGenerationStatus(wire_version="1", generation=plan_to_wire(plan), state=phase.value)
