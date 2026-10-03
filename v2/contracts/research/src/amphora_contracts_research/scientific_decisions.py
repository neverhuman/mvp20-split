"""Immutable purpose-bound decisions and explicit consumer references; no Runtime authority."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from pydantic import Field

from .eligibility import EligibilityAssessment
from .observations import ObservationRevisionRef
from .synthesis import SynthesisAssessment


class ScientificDecisionRef(WireModel):
    scope: Scope
    kind: Literal["eligibility","synthesis"]
    decision_id: Identifier
    sha256: Digest


class EligibilityDecision(WireModel):
    wire_version: Literal["1"]
    reference: ScientificDecisionRef
    actor_id: Identifier
    assessment: EligibilityAssessment
    sources: Annotated[tuple[ArtifactRef, ...],Field(min_length=1,max_length=128)]
    observations: Annotated[tuple[ObservationRevisionRef, ...],Field(max_length=1024)]


class SynthesisDecision(WireModel):
    wire_version: Literal["1"]
    reference: ScientificDecisionRef
    actor_id: Identifier
    assessment: SynthesisAssessment
    sources: Annotated[tuple[ArtifactRef, ...],Field(min_length=1,max_length=128)]


class ScientificImpactPage(WireModel):
    wire_version: Literal["1"]
    policy: Literal["future_campaigns_only"]
    decisions: Annotated[tuple[ScientificDecisionRef, ...],Field(max_length=128)]
    next_after: ScientificDecisionRef | None


class DecisionConsumerPage(WireModel):
    wire_version: Literal["1"]
    decision: ScientificDecisionRef
    consumers: Annotated[tuple[ArtifactRef, ...],Field(max_length=128)]
    next_after: Identifier | None
