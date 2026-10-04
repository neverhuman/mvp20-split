"""Logical request and physical-attempt identities, distinct from execution acceptance."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, Scope, WireModel
from amphora_contracts_graph_runtime import GraphReadCut
from pydantic import Field

from .context import ContextManifest, TokenCount


class EngagementRef(WireModel):
    scope: Scope
    engagement_id: Identifier


class EngagementRequest(WireModel):
    schema_version: Literal["1"] = "1"
    reference: EngagementRef
    actor_id: Identifier
    purpose: Literal["knowledge_decomposition", "campaign_proposal", "supervision"]
    decision_scope: Digest
    runtime_cut: GraphReadCut | None
    context: ContextManifest


class ProviderAttemptRef(WireModel):
    engagement: EngagementRef
    request_sha256: Digest
    ordinal: Annotated[int, Field(ge=1, le=16)]


class ProviderUsage(WireModel):
    input_tokens: TokenCount | None
    output_tokens: TokenCount | None
    accounting_units: Annotated[int, Field(ge=0, le=9007199254740991)] | None
    certainty: Literal["reported", "unknown"]
