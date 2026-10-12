"""Operator configuration DTOs; domain factories own authority and defaults."""
from typing import Annotated, Literal
from amphora_contracts_core import Identifier, SafePositiveInt, WireModel
from amphora_contracts_planning import EngagementRequest
from pydantic import Field


class FutureLimits(WireModel):
    max_nodes: Annotated[int, Field(ge=1, le=4096)]
    max_scopes: Annotated[int, Field(ge=1, le=1024)]
    max_depth: Annotated[int, Field(ge=0, le=16)]
    max_iterations: Annotated[int, Field(ge=1, le=10000)]
    max_tool_timeout: Annotated[int, Field(ge=1, le=86400)]
    side_effects: Annotated[tuple[Literal['pure', 'idempotent', 'external'], ...], Field(min_length=1, max_length=3)]


class PolicyRecord(WireModel):
    profile: Literal['planning-curation-policy.v1']
    policy_id: Identifier
    template: EngagementRequest
    future: FutureLimits
    eligibility_context: Identifier
    reservation_units: SafePositiveInt
