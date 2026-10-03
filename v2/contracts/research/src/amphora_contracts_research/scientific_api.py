"""Reference selections and historical scientific outcomes; submission cannot replace result bytes."""
from typing import Annotated, Literal

from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_core import ArtifactRef, Identifier, Scope, WireModel
from pydantic import Field

from .observations import ObservationRevisionRef
from .scientific_decisions import EligibilityDecision, ScientificDecisionRef, SynthesisDecision
from .scientific_inputs import ScientificAssessmentRequest


class ScientificAssessmentPending(WireModel):
    status: Literal["pending"]


class ScientificAssessmentComplete(WireModel):
    status: Literal["assessed"]
    decision: EligibilityDecision | SynthesisDecision


class ScientificAssessmentStatus(WireModel):
    wire_version: Literal["1"]
    request: ScientificAssessmentRequest
    actor_id: Identifier
    outcome: Annotated[ScientificAssessmentPending | ScientificAssessmentComplete,Field(discriminator="status")]


class LabIntakeSelection(WireModel):
    kind: Literal["lab-intake"]
    scope: Scope
    intake_id: Identifier


class ScientificDecisionSelection(WireModel):
    kind: Literal["decision"]
    reference: ScientificDecisionRef


ScientificResultSelection = Annotated[LabIntakeSelection | ScientificDecisionSelection,Field(discriminator="kind")]


class ScientificPublicationRequest(WireModel):
    wire_version: Literal["1"]
    target: ScientificResultSelection


class ScientificPublicationPending(WireModel):
    status: Literal["pending"]


class ScientificPublicationComplete(WireModel):
    status: Literal["published"]
    derivation: DerivationReceipt


class ScientificPublicationFailed(WireModel):
    status: Literal["failed"]
    code: Identifier
    external_effects: Literal["possible"]


class ScientificPublicationStatus(WireModel):
    wire_version: Literal["1"]
    request: ScientificPublicationRequest
    actor_id: Identifier
    outcome: Annotated[ScientificPublicationPending | ScientificPublicationComplete | ScientificPublicationFailed,
                       Field(discriminator="status")]


class ScientificImpactRequest(WireModel):
    wire_version: Literal["1"]
    source: ArtifactRef | ObservationRevisionRef
    after: ScientificDecisionRef | None
    limit: Annotated[int,Field(ge=1,le=128)]


class RegisterScientificConsumer(WireModel):
    wire_version: Literal["1"]
    decision: ScientificDecisionRef
    consumer: ArtifactRef


class ScientificConsumersRequest(WireModel):
    wire_version: Literal["1"]
    decision: ScientificDecisionRef
    after: Identifier | None
    limit: Annotated[int,Field(ge=1,le=128)]
