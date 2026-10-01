"""Immutable identity observations; no scientific acceptance authority."""

from typing import Literal

from amphora_contracts_core import Identifier, WireModel
from amphora_contracts_research import IdentityResolution

from .references import ConversionTraceRef


class ObserveSourceIdentity(WireModel):
    wire_version: Literal["1"]
    observation_id: Identifier
    trace: ConversionTraceRef


class SourceIdentityObservation(WireModel):
    wire_version: Literal["1"]
    request: ObserveSourceIdentity
    kind: Literal["not_applicable", "unresolved", "research_identity"]
    resolution: IdentityResolution | None
    scientific_authority: Literal["none"]


class SourceIdentityStatus(WireModel):
    wire_version: Literal["1"]
    request: ObserveSourceIdentity
    result: SourceIdentityObservation | None
