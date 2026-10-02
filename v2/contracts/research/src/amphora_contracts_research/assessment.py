"""Synthetic assessment wire shapes; issuer trust and decisions remain Research-owned."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from pydantic import Field, field_validator

from .questions import EvidenceNeed, EvidenceNeedRef, ResearchQuestion, ResearchQuestionRef

EvidenceCategory = Literal["opinion", "simulation", "observation", "independent_replication"]
EvidenceDisposition = Literal["supported", "contradicted", "unknown"]


class AssessmentProfileRef(WireModel):
    scope: Scope
    profile_id: Identifier
    version: Identifier
    sha256: Digest


class AssessmentRequirement(WireModel):
    need: EvidenceNeed
    categories: Annotated[tuple[EvidenceCategory, ...], Field(min_length=1, max_length=4)]
    issuers: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=32)]


class AssessmentTarget(WireModel):
    criterion_id: Identifier
    target_sha256: Digest


class EvidenceAssessmentProfile(WireModel):
    wire_version: Literal["1"]
    profile_id: Identifier
    version: Identifier
    authority: Literal["synthetic"]
    purpose: Identifier
    question: ResearchQuestion
    subject: ArtifactRef
    targets: Annotated[tuple[AssessmentTarget, ...], Field(min_length=1, max_length=32)]
    answer_publishers: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=32)]
    requirements: Annotated[tuple[AssessmentRequirement, ...], Field(min_length=1, max_length=128)]


class AssessmentAnswerRef(WireModel):
    criterion_id: Identifier
    artifact: ArtifactRef


class EvidenceAssessmentRequest(WireModel):
    wire_version: Literal["1"]
    assessment_id: Identifier
    profile: AssessmentProfileRef
    question: ResearchQuestionRef
    answers: Annotated[tuple[AssessmentAnswerRef, ...], Field(max_length=32)]
    receipts: Annotated[tuple[ArtifactRef, ...], Field(max_length=256)]


class EvidenceGap(WireModel):
    criterion_id: Identifier
    need: EvidenceNeedRef
    reason: Literal["missing_answer", "answer_contradicted", "answer_unknown", "no_matching_evidence",
                    "evidence_contradicted", "evidence_conflict"]


class AssessmentNeedDecision(WireModel):
    criterion_id: Identifier
    need: EvidenceNeedRef
    supporting: Annotated[tuple[ArtifactRef, ...], Field(max_length=256)]
    contradicting: Annotated[tuple[ArtifactRef, ...], Field(max_length=256)]
    gap: EvidenceGap | None


class AssessmentReceiptReview(WireModel):
    receipt: ArtifactRef
    reason: Literal["supporting", "contradicting", "unknown", "scope_mismatch", "need_revision_mismatch",
                    "criterion_mismatch", "missing_answer", "answer_revision_mismatch", "method_mismatch",
                    "context_mismatch", "category_mismatch", "untrusted_issuer", "purpose_mismatch",
                    "authority_mismatch"]


class EvidenceAssessment(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    request: EvidenceAssessmentRequest
    actor_id: Identifier
    purpose: Identifier
    subject: ArtifactRef
    answered: bool
    disposition: EvidenceDisposition
    sufficient: bool
    scientifically_established: Literal[False]
    needs: Annotated[tuple[AssessmentNeedDecision, ...], Field(min_length=1, max_length=4096)]
    reviews: Annotated[tuple[AssessmentReceiptReview, ...], Field(max_length=256)]

    @field_validator("scientifically_established", mode="before")
    @classmethod
    def literal_false(cls, value: object) -> bool:
        # Python equates 0 and False; JSON Schema does not. Preserve strict wire parity.
        if value is not False:
            raise ValueError("scientifically_established_must_be_false")
        return False


class PendingAssessment(WireModel):
    status: Literal["pending"]


class FailedAssessment(WireModel):
    status: Literal["failed"]
    code: Identifier


class CompletedAssessment(WireModel):
    status: Literal["assessed"]
    assessment: EvidenceAssessment


class EvidenceAssessmentStatus(WireModel):
    wire_version: Literal["1"]
    request: EvidenceAssessmentRequest
    actor_id: Identifier
    outcome: Annotated[PendingAssessment | FailedAssessment | CompletedAssessment, Field(discriminator="status")]
