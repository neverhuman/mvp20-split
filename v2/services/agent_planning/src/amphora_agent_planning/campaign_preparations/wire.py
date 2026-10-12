"""Private journal DTOs; domain factories own validation and assembly behavior."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_planning import EngagementRef
from pydantic import Field, JsonValue

Lane = Literal['curation_knowledge', 'curation', 'artifact', 'research', 'research_view', 'graph', 'registry_scan', 'registry_inventory',
               'registry_exact', 'runtime', 'runtime_schema', 'retrieval']


class ObservationRecord(WireModel):
    kind: Identifier
    identity: dict[str, JsonValue]
    sha256: Digest


class CandidateRecord(WireModel):
    lane: Lane
    identity: dict[str, JsonValue]
    payload_sha256: Digest
    required: bool
    included: bool
    observations: Annotated[tuple[ObservationRecord, ...], Field(max_length=8192)]


class PacketRecord(WireModel):
    sha256: Digest
    size_bytes: Annotated[int, Field(ge=1, le=8388608)]
    fit: dict[str, JsonValue]


class PreparationRecord(WireModel):
    profile: Literal['planning-campaign-preparation.v1']
    authority: Literal['historical_input_only']
    engagement: EngagementRef
    request_sha256: Digest
    plan_sha256: Digest
    packet: PacketRecord
    candidates: Annotated[tuple[CandidateRecord, ...], Field(min_length=1, max_length=900)]
