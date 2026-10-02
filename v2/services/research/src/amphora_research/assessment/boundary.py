"""Configured profiles and explicit domain-to-wire conversion; authentication remains an adapter duty."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_research import (
    AssessmentNeedDecision,
    AssessmentProfileRef,
    AssessmentReceiptReview,
    EvidenceAssessment,
    EvidenceAssessmentProfile,
    EvidenceAssessmentRequest,
    EvidenceGap,
)

from ..identity.questions import QuestionDefinition
from .policy import (
    AssessmentError,
    AssessmentPolicy,
    CandidateAnswer,
    EvidenceObservation,
    NeedRequirement,
    _identifier,
)


@dataclass(frozen=True)
class ConfiguredAssessment:
    document: EvidenceAssessmentProfile
    policy: AssessmentPolicy

    @classmethod
    def from_wire(cls, document: EvidenceAssessmentProfile) -> "ConfiguredAssessment":
        question = QuestionDefinition(document.question)
        if document.subject.scope != question.record.reference.scope:
            raise AssessmentError("subject_scope_mismatch")
        criteria = [item.criterion_id for item in document.targets]
        if len(criteria) != len(set(criteria)):
            raise AssessmentError("duplicate_target")
        if set(criteria) != {item.criterion_id for item in question.record.criteria}:
            raise AssessmentError("target_coverage_mismatch")
        if len(document.answer_publishers) != len(set(document.answer_publishers)):
            raise AssessmentError("duplicate_answer_publisher")
        for item in document.requirements:
            if len(item.categories) != len(set(item.categories)) or len(item.issuers) != len(set(item.issuers)):
                raise AssessmentError("duplicate_trust_entry")
        requirements = tuple(NeedRequirement(item.need, frozenset(item.categories), frozenset(item.issuers))
                             for item in document.requirements)
        policy = AssessmentPolicy(question, document.profile_id, document.version, document.purpose, requirements)
        return cls(document, policy)

    @property
    def reference(self) -> AssessmentProfileRef:
        # Full public document binds adapter trust/targets as well as the private decision policy.
        content = json.dumps(self.document.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
        return AssessmentProfileRef(scope=self.document.question.reference.scope,
                                    profile_id=self.document.profile_id, version=self.document.version,
                                    sha256=hashlib.sha256(content).hexdigest())

    def bind(self, request: EvidenceAssessmentRequest, actor_id: str, scope: Scope) -> "BoundAssessment":
        _identifier(actor_id)
        if scope != self.reference.scope or request.profile.scope != scope or request.question.scope != scope:
            raise AssessmentError("assessment_scope_mismatch")
        if request.profile != self.reference:
            raise AssessmentError("profile_mismatch")
        if request.question != self.document.question.reference:
            raise AssessmentError("question_revision_mismatch")
        criteria = {item.criterion_id for item in self.document.targets}
        selected = [item.criterion_id for item in request.answers]
        if len(selected) != len(set(selected)):
            raise AssessmentError("duplicate_answer")
        if not set(selected) <= criteria:
            raise AssessmentError("unknown_criterion")
        if any(item.scope != scope for item in (*request.receipts, *(a.artifact for a in request.answers))):
            raise AssessmentError("artifact_scope_mismatch")
        if len({item.artifact_id for item in request.receipts}) != len(request.receipts):
            raise AssessmentError("duplicate_receipt")
        return BoundAssessment(self, request, actor_id)


@dataclass(frozen=True)
class BoundAssessment:
    configured: ConfiguredAssessment
    request: EvidenceAssessmentRequest
    actor_id: str

    def evaluate(self, answers: tuple[CandidateAnswer, ...],
                 observations: tuple[EvidenceObservation, ...]) -> EvidenceAssessment:
        """Only call after authenticated peer resolution; equality is not authentication."""
        selected = {(item.criterion_id, item.artifact) for item in self.request.answers}
        if len(answers) != len(selected) or {(item.criterion_id, item.artifact) for item in answers} != selected:
            raise AssessmentError("resolved_answer_mismatch")
        if (len(observations) != len(self.request.receipts)
                or {item.receipt for item in observations} != set(self.request.receipts)):
            raise AssessmentError("resolved_receipt_mismatch")
        decision = self.configured.policy.assess(answers, observations)
        needs = tuple(AssessmentNeedDecision(
            criterion_id=item.criterion_id, need=item.need, supporting=item.supporting,
            contradicting=item.contradicting,
            gap=None if item.gap is None else EvidenceGap(
                criterion_id=item.criterion_id, need=item.need, reason=item.gap),
        ) for item in decision.needs)
        reviews = tuple(AssessmentReceiptReview(receipt=item.observation.receipt, reason=item.reason)
                        for item in decision.reviews)
        return EvidenceAssessment(
            wire_version="1", authority="synthetic", request=self.request, actor_id=self.actor_id,
            purpose=self.configured.document.purpose, subject=self.configured.document.subject,
            answered=decision.answered, disposition=decision.disposition, sufficient=decision.sufficient,
            scientifically_established=False, needs=needs, reviews=reviews,
        )
