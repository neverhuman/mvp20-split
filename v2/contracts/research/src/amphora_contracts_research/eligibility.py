"""Purpose-bound synthetic decision documents; submitted claims are not trusted verdicts."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from pydantic import Field

from .identity import CandidateRevisionRef, MaterialStateRevisionRef, SampleRevisionRef
from .observations import ObservationRevisionRef

EligibilityKind = Literal["measurement","model","synthesis"]
CriterionDisposition = Literal["supported","contradicted","unknown"]


class EligibilitySubject(WireModel):
    candidate: CandidateRevisionRef
    material_state: MaterialStateRevisionRef | None
    sample: SampleRevisionRef | None


class EligibilityContext(WireModel):
    subject: EligibilitySubject
    domain: Identifier
    purpose: Identifier
    conditions: ArtifactRef


class EligibilityEvidenceOrigin(WireModel):
    source: ArtifactRef
    method: SchemaRef
    kind: EligibilityKind
    authority: Literal["synthetic","scientific"]
    observation: ObservationRevisionRef | None


class EligibilityClaim(WireModel):
    criterion_id: Identifier
    context: EligibilityContext
    origin: EligibilityEvidenceOrigin
    disposition: CriterionDisposition
    flags: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class EligibilityRequirement(WireModel):
    criterion_id: Identifier
    kind: EligibilityKind
    method: SchemaRef
    required: bool
    excluded_flags: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class EligibilityProfile(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    reference: SchemaRef
    context: EligibilityContext
    requirements: Annotated[tuple[EligibilityRequirement, ...],Field(min_length=1,max_length=128)]


class EligibilityClaimReview(WireModel):
    claim: EligibilityClaim
    reasons: Annotated[tuple[Literal["applicability_mismatch","authority_mismatch","undeclared_criterion",
                                   "evidence_kind_mismatch","method_mismatch","quality_excluded_by_policy"], ...],Field(max_length=6)]


class EligibilityCriterionDecision(WireModel):
    criterion_id: Identifier
    disposition: CriterionDisposition
    reason: Literal["conflicting_evidence","explicit_uncertainty","prerequisite_failed","bounded_support","missing_eligible_evidence"]


class EligibilityAssessment(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    policy: EligibilityProfile
    disposition: Literal["eligible","ineligible","unknown"]
    criteria: Annotated[tuple[EligibilityCriterionDecision, ...],Field(min_length=1,max_length=128)]
    reviews: Annotated[tuple[EligibilityClaimReview, ...],Field(max_length=1024)]
    focus: Annotated[tuple[Identifier, ...],Field(max_length=128)]
