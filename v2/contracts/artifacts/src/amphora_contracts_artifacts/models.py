"""Scoped immutable storage and retention receipts; no scientific authority."""

from typing import Annotated, Literal

from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Identifier,
    SchemaRef,
    Scope,
    WireModel,
)
from pydantic import Field


class ContentDescriptor(WireModel):
    sha256: Digest
    size_bytes: Annotated[int, Field(ge=0, le=9007199254740991)]
    media_type: Annotated[str, Field(min_length=3, max_length=128, pattern=r"^[^\s/]+/[^\s/]+$")]
    schema_ref: SchemaRef


class BeginUpload(WireModel):
    content: ContentDescriptor


class FinalizeArtifact(WireModel):
    upload_id: Identifier
    content: ContentDescriptor


class CompletionIntentBinding(WireModel):
    runtime_owner: Identifier
    intent_id: Identifier
    semantic_completion_sha256: Digest
    output_binding: Identifier


class ReserveArtifact(WireModel):
    artifact: ArtifactRef
    intent: CompletionIntentBinding


class ConfirmRetention(WireModel):
    reservation_id: Identifier
    intent_id: Identifier
    runtime_receipt_id: Identifier


class ReconcileReservation(WireModel):
    reservation_id: Identifier


class ReservationBinding(WireModel):
    reservation_id: Identifier
    artifact: ArtifactRef
    intent: CompletionIntentBinding


class CommittedIntentProof(WireModel):
    status: Literal["committed"]
    runtime_receipt_id: Identifier


class AbortedIntentProof(WireModel):
    status: Literal["aborted"]
    runtime_receipt_id: Identifier
    reason_code: Identifier


class Reserved(WireModel):
    status: Literal["reserved"]
    binding: ReservationBinding


class Confirmed(WireModel):
    status: Literal["confirmed"]
    binding: ReservationBinding
    proof: CommittedIntentProof


class Released(WireModel):
    status: Literal["released"]
    binding: ReservationBinding
    proof: AbortedIntentProof


class ReservationReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    outcome: Annotated[Reserved | Confirmed | Released, Field(discriminator="status")]


class UploadReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    upload_id: Identifier
    scope: Scope
    content: ContentDescriptor


class FinalizedReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    upload_id: Identifier
    artifact: ArtifactRef


class UploadContentReceipt(WireModel):
    """Verified provisional bytes only; never an ArtifactRef."""

    schema_version: Literal["1"] = "1"
    upload_id: Identifier
    attempt_id: Identifier
    generation: Annotated[int, Field(ge=1, le=9007199254740991)]
    status: Literal["streamed"] = "streamed"


class PendingIntentProof(WireModel):
    status: Literal["prepared", "unknown"]


class RuntimeOutcome(WireModel):
    """Authenticated runtime projection for one exact reservation binding."""

    schema_version: Literal["1"] = "1"
    binding: ReservationBinding
    proof: Annotated[CommittedIntentProof | AbortedIntentProof | PendingIntentProof, Field(discriminator="status")]
