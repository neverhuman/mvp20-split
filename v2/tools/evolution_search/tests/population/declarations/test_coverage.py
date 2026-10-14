import hashlib

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import EvaluationDeclarationManifest, EvaluationResolutionManifest, MembershipPageReference, membership_manifest_schema, population_record_schema
from amphora_evolution_search.population import BoundEvaluation, DeclaredEvaluations, PopulationArtifact, RecordPages, canonical


def test_late_input_binding_preserves_declared_occurrence(assessment_factory):
    evidence, _ = assessment_factory
    membership = evidence.evaluations.membership
    declaration = DeclaredEvaluations.primary(membership)
    original_digest = declaration.digest
    resolved = declaration.resolve(evidence.evaluations.keys)
    key = resolved.keys[0]
    intermediate = key.record.material.model_copy(update={"artifact_id": "accepted-intermediate", "sha256": "d" * 64})
    late = BoundEvaluation(membership, key.record.model_copy(update={"inputs": (*key.record.inputs, intermediate)}))
    replacement = tuple(late if item.digest == key.digest else item for item in resolved.keys)
    updated = declaration.resolve(replacement)
    assert updated.digest != resolved.digest
    assert declaration.digest == original_digest
    assert declaration.resolve(tuple(reversed(replacement))) == updated


def test_success_only_or_unplanned_occurrence_cannot_close_generation(assessment_factory):
    evidence, _ = assessment_factory
    declaration = DeclaredEvaluations.primary(evidence.evaluations.membership)
    with pytest.raises(ValueError):
        declaration.resolve(evidence.evaluations.keys[:-1])
    key = evidence.evaluations.keys[0]
    extra = BoundEvaluation(key.membership, key.record.model_copy(update={"occurrence_id": "unplanned"}))
    with pytest.raises(ValueError, match="declaration_resolution_coverage"):
        declaration.resolve((*evidence.evaluations.keys, extra))
    with pytest.raises(ValueError, match="declaration_duplicate"):
        DeclaredEvaluations(declaration.membership, (*declaration.slots, declaration.slots[0]))


def test_declared_slots_pages_and_resolution_manifest_bind_independent_sources(assessment_factory):
    evidence, _ = assessment_factory
    membership = evidence.evaluations.membership
    declaration = DeclaredEvaluations.primary(membership)
    def artifact(name, schema, record=None):
        raw = canonical(record) if record is not None else b"{}"
        return PopulationArtifact(ArtifactRef(artifact_id=name, scope=membership.identity.scope,
            schema_ref=schema, media_type="application/json", sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)), raw)
    pages = RecordPages(membership.identity, "population.evaluation-slot-page", declaration.slots).pack()
    refs = tuple(MembershipPageReference(ordinal=i, members=len(page.records),
        artifact=artifact("page" + str(i), population_record_schema("population.evaluation-slot-page"), page).reference)
        for i, page in enumerate(pages))
    cohort_ref = artifact("cohort", membership_manifest_schema()).reference
    root = EvaluationDeclarationManifest(schema_version="1", profile="population-evaluation-declaration-manifest-v1",
        generation=membership.identity, membership=cohort_ref, slot_set_sha256=declaration.digest,
        slot_count=len(declaration.slots), pages=refs)
    retained = artifact("declaration", population_record_schema("population.evaluation-declarations"), root)
    assert DeclaredEvaluations.verified(membership, cohort_ref, retained, tuple(canonical(p) for p in pages)) == declaration
    evaluated = artifact("evaluations", population_record_schema("population.evaluation-manifest")).reference
    resolution = EvaluationResolutionManifest(schema_version="1", profile="population-evaluation-resolution-manifest-v1",
        generation=membership.identity, declarations=retained.reference, evaluations=evaluated,
        slot_set_sha256=declaration.digest, evaluation_set_sha256=evidence.evaluations.digest)
    declaration.verify_resolution(retained.reference, evaluated, resolution, evidence.evaluations)
    with pytest.raises(ValueError, match="resolution_key_set"):
        declaration.verify_resolution(retained.reference, evaluated,
            resolution.model_copy(update={"evaluation_set_sha256": "f" * 64}), evidence.evaluations)
