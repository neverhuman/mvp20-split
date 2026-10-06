"""Planning completion readback, distinct from physical attempts and Runtime winners."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, WireModel
from amphora_contracts_planning import EngagementRef, ProviderAttemptRef
from pydantic import Field

from .requests import SupervisionRef

CheckpointStopReason = Literal[
    'proposed', 'abstained', 'policy_rejected', 'attempt_limit',
    'checkpoint_deadline', 'execution_processing_unavailable', 'required_artifact_unavailable',
    'required_packet_size', 'required_input_limit', 'budget_template_unavailable', 'provider_unconfigured',
    'token_budget_exhausted', 'accounting_budget_exhausted', 'provider_usage_overage',
    'repair_attempt_budget_exhausted', 'repair_token_budget_exhausted', 'repair_accounting_budget_exhausted',
]


class CheckpointAttemptResult(WireModel):
    attempt: ProviderAttemptRef
    observation_sha256: Digest
    status: Literal['proposed', 'abstained', 'invalid', 'unavailable', 'policy_rejected', 'unknown']


class CheckpointExecutionReport(WireModel):
    schema_version: Literal['1'] = '1'
    reference: SupervisionRef
    request_sha256: Digest
    engagement: EngagementRef
    planning_request_sha256: Digest
    stop_reason: CheckpointStopReason
    attempts: Annotated[tuple[CheckpointAttemptResult, ...], Field(max_length=16)]
