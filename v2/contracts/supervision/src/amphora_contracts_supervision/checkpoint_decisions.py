"""Checkpoint owner readback supports fallback before any Planning request exists."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_core import Digest, Identifier, SafePositiveInt, WireModel
from amphora_contracts_graph_runtime import ScalarValue
from pydantic import Field

from .decisions import ContinuedUnchanged, RetainedProposal
from .requests import SupervisionRef


class EffectiveFieldChange(WireModel):
    field_name: Identifier
    previous_value_sha256: Digest
    value: ScalarValue


class AppliedFields(WireModel):
    kind: Literal['adjusted_materialization_fields']
    target: ActivationPath
    selection_sha256: Digest
    changes: Annotated[tuple[EffectiveFieldChange, ...], Field(min_length=1, max_length=64)]


class CheckpointPending(WireModel):
    kind: Literal['pending']
    stage: Literal['checkpoint', 'requested', 'dispatched', 'proposed']
    request_sha256: Digest | None


class CheckpointModelAccepted(WireModel):
    kind: Literal['model_accepted']
    request_sha256: Digest
    response_sha256: Digest
    effect: Annotated[AppliedFields | RetainedProposal | ContinuedUnchanged, Field(discriminator='kind')]


class CheckpointFallback(WireModel):
    kind: Literal['fallback']
    action: Literal['continue_unchanged', 'block_target']
    reason_code: Identifier


class CheckpointCancelled(WireModel):
    kind: Literal['cancelled']
    reason_code: Identifier


class CheckpointDecision(WireModel):
    schema_version: Literal['1'] = '1'
    profile: Literal['checkpoint-decision.v1'] = 'checkpoint-decision.v1'
    reference: SupervisionRef
    revision: SafePositiveInt
    checkpoint_seed_sha256: Digest
    outcome: Annotated[CheckpointPending | CheckpointModelAccepted | CheckpointFallback | CheckpointCancelled,
                       Field(discriminator='kind')]
