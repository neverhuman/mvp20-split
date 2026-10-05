"""Observed Planning output is a candidate/diagnostic, never a Runtime decision."""

from typing import Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from amphora_contracts_planning import TaskProviderObservation

from .requests import SupervisionRef


class SupervisionResponse(WireModel):
    schema_version: Literal['1'] = '1'
    response_id: Identifier
    reference: SupervisionRef
    request_sha256: Digest
    observation: TaskProviderObservation
    capture: ArtifactRef | None


class CancelSupervision(WireModel):
    schema_version: Literal['1'] = '1'
    cancellation_id: Identifier
    reference: SupervisionRef
    request_sha256: Digest
    reason_code: Identifier
