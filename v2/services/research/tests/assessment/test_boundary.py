import json
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    AssessmentAnswerRef,
    AssessmentRequirement,
    AssessmentTarget,
    EvidenceAssessmentProfile,
    EvidenceAssessmentRequest,
)
from amphora_research.assessment.boundary import ConfiguredAssessment
from amphora_research.assessment.policy import AssessmentError

from .test_policy import OTHER, SCOPE, artifact, fixture


def configured():
    policy, answer, evidence = fixture()
    document = EvidenceAssessmentProfile(
        wire_version="1", profile_id=policy.policy_id, version=policy.version, authority="synthetic",
        purpose=policy.purpose, question=policy.question.record, subject=artifact("subject"),
        targets=(AssessmentTarget(criterion_id="c", target_sha256="c" * 64),),
        answer_publishers=("knowledge-publisher",),
        requirements=tuple(AssessmentRequirement(need=r.need, categories=tuple(sorted(r.categories)),
                                                issuers=tuple(sorted(r.issuers))) for r in policy.requirements))
    owner = ConfiguredAssessment.from_wire(document)
    request = EvidenceAssessmentRequest(
        wire_version="1", assessment_id="assessment-1", profile=owner.reference,
        question=document.question.reference,
        answers=(AssessmentAnswerRef(criterion_id="c", artifact=answer.artifact),), receipts=(evidence.receipt,))
    return owner, request, answer, evidence


def test_exact_bind_and_explicit_projection_preserve_domain_result():
    owner, request, answer, evidence = configured()
    record = owner.bind(request, "reader", SCOPE).evaluate((answer,), (evidence,))
    assert record.request == request and record.actor_id == "reader"
    assert record.answered and record.sufficient and not record.scientifically_established
    assert record.needs[0].supporting == (evidence.receipt,)
    assert record.reviews[0].reason == "supporting"
    assert record.subject == owner.document.subject
    assert type(record).model_validate_json(record.model_dump_json()) == record
    missing = request.model_copy(update={"answers": (), "receipts": ()})
    gap = owner.bind(missing, "reader", SCOPE).evaluate((), ())
    assert gap.needs[0].gap.reason == "missing_answer"
    assert not gap.answered and gap.disposition == "unknown"


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda d: d.model_copy(update={"subject": artifact("subject", scope=OTHER)}), "subject_scope_mismatch"),
    (lambda d: d.model_copy(update={"targets": d.targets * 2}), "duplicate_target"),
    (lambda d: d.model_copy(update={"targets": ()}), "target_coverage_mismatch"),
    (lambda d: d.model_copy(update={"answer_publishers": d.answer_publishers * 2}), "duplicate_answer_publisher"),
    (lambda d: d.model_copy(update={"requirements": (d.requirements[0].model_copy(
        update={"categories": ("observation", "observation")}),)}), "duplicate_trust_entry"),
    (lambda d: d.model_copy(update={"requirements": (d.requirements[0].model_copy(
        update={"issuers": ("issuer", "issuer")}),)}), "duplicate_trust_entry"),
])
def test_profile_behavior_rejects_invalid_bindings(mutation, code):
    owner, *_ = configured()
    with pytest.raises(AssessmentError, match=code):
        ConfiguredAssessment.from_wire(mutation(owner.document))


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda r: r.model_copy(update={"profile": r.profile.model_copy(update={"scope": OTHER})}),
     "assessment_scope_mismatch"),
    (lambda r: r.model_copy(update={"profile": r.profile.model_copy(update={"sha256": "d" * 64})}),
     "profile_mismatch"),
    (lambda r: r.model_copy(update={"question": r.question.model_copy(update={"revision": 2})}),
     "question_revision_mismatch"),
    (lambda r: r.model_copy(update={"answers": r.answers * 2}), "duplicate_answer"),
    (lambda r: r.model_copy(update={"answers": (r.answers[0].model_copy(update={"criterion_id": "other"}),)}),
     "unknown_criterion"),
    (lambda r: r.model_copy(update={"receipts": (artifact("receipt", scope=OTHER),)}), "artifact_scope_mismatch"),
    (lambda r: r.model_copy(update={"receipts": r.receipts * 2}), "duplicate_receipt"),
])
def test_request_invariants_are_owned_not_dto_algorithms(mutation, code):
    owner, request, *_ = configured()
    with pytest.raises(AssessmentError, match=code):
        owner.bind(mutation(request), "reader", SCOPE)


def test_authenticated_scope_and_resolved_references_must_match_request():
    owner, request, answer, evidence = configured()
    with pytest.raises(AssessmentError, match="assessment_scope_mismatch"):
        owner.bind(request, "reader", OTHER)
    bound = owner.bind(request, "reader", SCOPE)
    with pytest.raises(AssessmentError, match="resolved_answer_mismatch"):
        bound.evaluate((), (evidence,))
    with pytest.raises(AssessmentError, match="resolved_answer_mismatch"):
        bound.evaluate((replace(answer, artifact=artifact("another")),), (evidence,))
    with pytest.raises(AssessmentError, match="resolved_receipt_mismatch"):
        bound.evaluate((answer,), ())
    with pytest.raises(AssessmentError, match="resolved_receipt_mismatch"):
        bound.evaluate((answer,), (replace(evidence, receipt=artifact("another")),))


def test_profile_fingerprint_covers_adapter_trust_and_expected_target():
    owner, *_ = configured()
    variants = [owner.document.model_copy(update={"answer_publishers": ("different",)}),
                owner.document.model_copy(update={"subject": artifact("another")}),
                owner.document.model_copy(update={"targets": (
                    AssessmentTarget(criterion_id="c", target_sha256="d" * 64),)})]
    assert len({owner.reference.sha256, *(ConfiguredAssessment.from_wire(d).reference.sha256 for d in variants)}) == 4
    assert ConfiguredAssessment.from_wire(EvidenceAssessmentProfile.model_validate_json(
        json.dumps(owner.document.model_dump(mode="json")))).reference == owner.reference
