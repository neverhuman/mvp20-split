"""Bounded evidence sufficiency for a pinned, explicitly synthetic decision."""

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_research import EvidenceNeed, EvidenceNeedRef

from ..identity.questions import QuestionDefinition

Disposition = Literal["supported", "contradicted", "unknown"]
CATEGORIES = frozenset({"opinion", "simulation", "observation", "independent_replication"})
DISPOSITIONS = frozenset({"supported", "contradicted", "unknown"})


class AssessmentError(ValueError):
    """Bounded safe failure code; never includes input document content."""


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
        raise AssessmentError("invalid_identifier")


@dataclass(frozen=True)
class NeedRequirement:
    need: EvidenceNeed
    categories: frozenset[str]
    issuers: frozenset[str]

    def __post_init__(self) -> None:
        if (not isinstance(self.categories, frozenset) or not self.categories
                or not self.categories <= CATEGORIES):
            raise AssessmentError("invalid_categories")
        if not isinstance(self.issuers, frozenset) or not 1 <= len(self.issuers) <= 32:
            raise AssessmentError("invalid_issuers")
        for issuer in self.issuers:
            _identifier(issuer)


@dataclass(frozen=True)
class CandidateAnswer:
    criterion_id: str
    artifact: ArtifactRef
    disposition: Disposition
    conflict: bool = False

    def __post_init__(self) -> None:
        _identifier(self.criterion_id)
        if self.disposition not in DISPOSITIONS:
            raise AssessmentError("invalid_disposition")
        if type(self.conflict) is not bool or (self.conflict and self.disposition != "unknown"):
            raise AssessmentError("invalid_answer_conflict")


@dataclass(frozen=True)
class EvidenceObservation:
    """Adapter projection only: constructing this object does not authenticate a receipt."""

    receipt: ArtifactRef
    need: EvidenceNeedRef
    criterion_id: str
    subject: ArtifactRef
    method: SchemaRef
    context: ArtifactRef
    category: str
    issuer: str
    purpose: str
    authority: str
    disposition: Disposition

    def __post_init__(self) -> None:
        _identifier(self.criterion_id)
        _identifier(self.issuer)
        _identifier(self.purpose)
        if self.category not in CATEGORIES:
            raise AssessmentError("invalid_category")
        if self.disposition not in DISPOSITIONS:
            raise AssessmentError("invalid_disposition")
        if self.authority not in {"synthetic", "scientific"}:
            raise AssessmentError("invalid_authority")


@dataclass(frozen=True)
class ReceiptReview:
    observation: EvidenceObservation
    reason: str


@dataclass(frozen=True)
class NeedDecision:
    criterion_id: str
    need: EvidenceNeedRef
    supporting: tuple[ArtifactRef, ...]
    contradicting: tuple[ArtifactRef, ...]
    gap: str | None


@dataclass(frozen=True)
class AssessmentDecision:
    policy_sha256: str
    answered: bool
    disposition: Disposition
    needs: tuple[NeedDecision, ...]
    reviews: tuple[ReceiptReview, ...]

    @property
    def sufficient(self) -> bool:
        return self.disposition == "supported" and all(item.gap is None for item in self.needs)

    @property
    def scientifically_established(self) -> bool:
        return False


@dataclass(frozen=True)
class AssessmentPolicy:
    question: QuestionDefinition
    policy_id: str
    version: str
    purpose: str
    requirements: tuple[NeedRequirement, ...]

    def __post_init__(self) -> None:
        for value in (self.policy_id, self.version, self.purpose):
            _identifier(value)
        if not isinstance(self.requirements, tuple) or not 1 <= len(self.requirements) <= 128:
            raise AssessmentError("invalid_requirement_count")
        seen = set()
        covered = set()
        for requirement in self.requirements:
            self.question.bind_need(requirement.need)
            # Two revisions of one need cannot silently double its policy weight.
            identity = requirement.need.reference.need_id
            if identity in seen:
                raise AssessmentError("duplicate_need")
            seen.add(identity)
            covered.update(requirement.need.criterion_ids)
        if covered != {criterion.criterion_id for criterion in self.question.record.criteria}:
            raise AssessmentError("uncovered_criterion")

    @property
    def sha256(self) -> str:
        document = {
            "format": "research.synthetic-assessment-policy.v1",
            "question": self.question.record.model_dump(mode="json"),
            "policy_id": self.policy_id, "version": self.version, "purpose": self.purpose,
            "requirements": [
                {"need": item.need.model_dump(mode="json"), "categories": sorted(item.categories),
                 "issuers": sorted(item.issuers)} for item in self.requirements
            ],
        }
        content = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def assess(self, answers: tuple[CandidateAnswer, ...],
               observations: tuple[EvidenceObservation, ...]) -> AssessmentDecision:
        if not isinstance(answers, tuple) or len(answers) > 32:
            raise AssessmentError("invalid_answer_count")
        if not isinstance(observations, tuple) or len(observations) > 256:
            raise AssessmentError("invalid_observation_count")
        criteria = {item.criterion_id for item in self.question.record.criteria}
        by_criterion = {}
        for answer in answers:
            if answer.criterion_id not in criteria:
                raise AssessmentError("unknown_criterion")
            if answer.criterion_id in by_criterion:
                raise AssessmentError("duplicate_answer")
            if answer.artifact.scope != self.question.record.reference.scope:
                raise AssessmentError("answer_scope_mismatch")
            by_criterion[answer.criterion_id] = answer
        seen = set()
        for observation in observations:
            identity = (observation.receipt.scope, observation.receipt.artifact_id)
            if identity in seen:
                raise AssessmentError("duplicate_receipt")
            seen.add(identity)
        # Sorting produces stable retained decisions regardless of arrival order.
        ordered = sorted(observations, key=lambda item: (
            item.receipt.scope.tenant_id, item.receipt.scope.project_id, item.receipt.artifact_id))
        reviews = tuple(ReceiptReview(item, self._review(item, by_criterion)) for item in ordered)
        needs = []
        for requirement in self.requirements:
            for criterion in requirement.need.criterion_ids:
                matching = [review for review in reviews
                            if review.observation.need == requirement.need.reference
                            and review.observation.criterion_id == criterion]
                supporting = tuple(review.observation.receipt for review in matching
                                   if review.reason == "supporting")
                contradicting = tuple(review.observation.receipt for review in matching
                                      if review.reason == "contradicting")
                answer = by_criterion.get(criterion)
                gap = _gap(answer, supporting, contradicting)
                needs.append(NeedDecision(criterion, requirement.need.reference, supporting, contradicting, gap))
        gaps = {item.gap for item in needs}
        if "evidence_conflict" in gaps or any(answer.conflict for answer in answers):
            disposition = "unknown"
        elif gaps & {"answer_contradicted", "evidence_contradicted"}:
            disposition = "contradicted"
        else:
            disposition = "supported" if gaps == {None} else "unknown"
        return AssessmentDecision(self.sha256, set(by_criterion) == criteria, disposition, tuple(needs), reviews)

    def _review(self, observation: EvidenceObservation, answers: dict[str, CandidateAnswer]) -> str:
        scope = self.question.record.reference.scope
        if any(ref.scope != scope for ref in (
                observation.receipt, observation.need, observation.subject, observation.context)):
            return "scope_mismatch"
        requirement = next((item for item in self.requirements
                            if item.need.reference == observation.need), None)
        if requirement is None:
            return "need_revision_mismatch"
        if observation.criterion_id not in requirement.need.criterion_ids:
            return "criterion_mismatch"
        answer = answers.get(observation.criterion_id)
        if answer is None:
            return "missing_answer"
        if observation.subject != answer.artifact:
            return "answer_revision_mismatch"
        if observation.method != requirement.need.method:
            return "method_mismatch"
        if observation.context != requirement.need.required_context:
            return "context_mismatch"
        if observation.category not in requirement.categories:
            return "category_mismatch"
        if observation.issuer not in requirement.issuers:
            return "untrusted_issuer"
        if observation.purpose != self.purpose:
            return "purpose_mismatch"
        if observation.authority != "synthetic":
            return "authority_mismatch"
        return {"supported": "supporting", "contradicted": "contradicting", "unknown": "unknown"}[
            observation.disposition]


def _gap(answer: CandidateAnswer | None, supporting: tuple[ArtifactRef, ...],
         contradicting: tuple[ArtifactRef, ...]) -> str | None:
    if supporting and contradicting:
        return "evidence_conflict"
    if answer is not None and answer.conflict:
        return "answer_unknown"
    if contradicting:
        return "evidence_contradicted"
    if answer is None:
        return "missing_answer"
    if answer.disposition != "supported":
        return "answer_contradicted" if answer.disposition == "contradicted" else "answer_unknown"
    return None if supporting else "no_matching_evidence"
