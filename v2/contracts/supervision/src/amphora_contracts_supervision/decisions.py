"""Owner-produced readbacks; model response commands cannot carry these effects."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ActivationPath, ScalarConstant
from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Identifier,
    SafePositiveInt,
    WireModel,
)
from pydantic import Field

from .requests import SupervisionRef


class EffectiveInputChange(WireModel):
    target: ActivationPath
    input_name: Identifier
    previous_value_sha256: Digest
    value: ScalarConstant


class AppliedInputs(WireModel):
    kind: Literal['adjusted_inputs']
    changes: Annotated[tuple[EffectiveInputChange, ...], Field(min_length=1, max_length=64)]


class RetainedProposal(WireModel):
    kind: Literal['future_campaign', 'evidence_request', 'abstained']
    proposal: ArtifactRef
    content_sha256: Digest


class ContinuedUnchanged(WireModel):
    kind: Literal['continued']


class PendingDecision(WireModel):
    status: Literal['pending']
    stage: Literal['requested', 'dispatched', 'proposed']


class AcceptedDecision(WireModel):
    status: Literal['accepted']
    source: Literal['model', 'fallback']
    effect: Annotated[AppliedInputs | RetainedProposal | ContinuedUnchanged, Field(discriminator='kind')]


class TerminalDecision(WireModel):
    status: Literal['rejected', 'stale', 'expired', 'failed', 'cancelled']
    source: Literal['model', 'fallback', 'cancellation', 'policy']
    reason_code: Identifier


class SupervisionDecision(WireModel):
    schema_version: Literal['1'] = '1'
    reference: SupervisionRef
    revision: SafePositiveInt
    request_sha256: Digest
    outcome: Annotated[PendingDecision | AcceptedDecision | TerminalDecision, Field(discriminator='status')]
