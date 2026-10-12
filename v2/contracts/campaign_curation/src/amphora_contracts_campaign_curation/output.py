"""Curation proposals and capability gaps, never tool or execution acceptance."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, SchemaRef, WireModel, Digest
from pydantic import Field

from amphora_contracts_planning import FutureCampaignDraft, CampaignUnresolvedPoint

Description = Annotated[str, Field(min_length=1, max_length=2048)]


class RequestedCapabilityPort(WireModel):
    name: Identifier
    representation: Identifier
    schema_ref: SchemaRef | None
    description: Description
    unit: Annotated[str, Field(min_length=1, max_length=64)] | None


class CapabilityGap(WireModel):
    """Model-local key; durable request identity is assigned by Planning."""

    gap_key: Identifier
    purpose: Description
    inputs: Annotated[tuple[RequestedCapabilityPort, ...], Field(max_length=32)]
    outputs: Annotated[tuple[RequestedCapabilityPort, ...], Field(min_length=1, max_length=32)]
    applicability: Annotated[tuple[Description, ...], Field(min_length=1, max_length=16)]
    evidence_need: Description
    acceptance_criteria: Annotated[tuple[Description, ...], Field(min_length=1, max_length=16)]
    graph_gap: Description


class CurationProposal(WireModel):
    kind: Literal['propose_campaign']
    candidate: FutureCampaignDraft
    gaps: Annotated[tuple[CapabilityGap, ...], Field(max_length=16)]


class CurationCapabilityRequest(WireModel):
    kind: Literal['request_capabilities']
    gaps: Annotated[tuple[CapabilityGap, ...], Field(min_length=1, max_length=16)]


class CurationAbstention(WireModel):
    kind: Literal['abstain']
    reason_code: Identifier


class CampaignCurationDraft(WireModel):
    schema_version: Literal['1'] = '1'
    profile: Literal['planning.campaign-curation-draft.v1']
    authority: Literal['proposal_only']
    scientific_authority: Literal['not_established']
    decision_scope: Digest
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]
    outcome: Annotated[CurationProposal | CurationCapabilityRequest | CurationAbstention,
                       Field(discriminator='kind')]
    unresolved: Annotated[tuple[CampaignUnresolvedPoint, ...], Field(max_length=64)]


def campaign_curation_draft_schema() -> SchemaRef:
    schema = CampaignCurationDraft.model_json_schema(mode='validation')
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'urn:amphora:planning.campaign-curation-draft:1:validation'
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False) + '\n').encode('utf-8')
    return SchemaRef(schema_id='planning.campaign-curation-draft', version='1',
                     sha256=hashlib.sha256(raw).hexdigest())
