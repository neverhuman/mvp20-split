"""Versioned typed candidates; canonical JSON is interpreted only by reviewed profiles."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel
from pydantic import Field

from .context import ProposalAction
from .engagement import ProviderAttemptRef, ProviderUsage


class TypedProposal(WireModel):
    schema_version: Literal["1"] = "1"
    output_schema: SchemaRef
    action: ProposalAction
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]
    payload_json: Annotated[str, Field(min_length=1, max_length=65536)]
    payload_sha256: Digest


class TaskProviderObservation(WireModel):
    schema_version: Literal["2"] = "2"
    attempt: ProviderAttemptRef
    status: Literal["proposed", "abstained", "invalid", "unavailable", "policy_rejected", "unknown"]
    reason_code: Identifier | None
    output_sha256: Digest
    captured_bytes: Annotated[int, Field(ge=0, le=65536)]
    output_complete: bool
    usage: ProviderUsage
    proposal: TypedProposal | None
