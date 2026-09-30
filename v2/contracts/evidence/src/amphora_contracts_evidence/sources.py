"""Source delivery records are separate from bytes and scientific acceptance."""

from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from pydantic import Field

from .references import RightsRevisionRef, SourceRevisionRef


class DeliveryIdentity(WireModel):
    issuer_id: Identifier
    delivery_id: Identifier


class AcquisitionMethod(WireModel):
    connector_id: Identifier
    connector_version: Identifier
    configuration_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    format: Literal["utf8_document", "synthetic_lab_json"]


class SourceRevision(WireModel):
    wire_version: Literal["1"]
    reference: SourceRevisionRef
    delivery: DeliveryIdentity
    method: AcquisitionMethod
    rights: RightsRevisionRef
    supersedes: SourceRevisionRef | None
    completeness: Literal["complete", "partial", "unknown"]

