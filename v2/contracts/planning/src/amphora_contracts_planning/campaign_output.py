"""Campaign candidates only; Runtime and scientific owners retain acceptance."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_campaigns import ExecutableCampaignV4, ScalarConstant
from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef
from pydantic import Field

from .campaign_context import CampaignAssessmentSelection

Description = Annotated[str, Field(min_length=1, max_length=2048)]


class CampaignNodeAddress(WireModel):
    scope_path: Annotated[tuple[Identifier, ...], Field(max_length=16)]
    node_id: Identifier


class CampaignEvidenceIntent(WireModel):
    question: ResearchQuestionRef
    needs: Annotated[tuple[EvidenceNeedRef, ...], Field(max_length=16)]
    assessments: Annotated[tuple[CampaignAssessmentSelection, ...], Field(max_length=16)]
    producer: CampaignNodeAddress | None
    expected_evidence: Description
    uncertainty: Description


class CampaignInputAdjustment(WireModel):
    target: CampaignNodeAddress
    input_name: Identifier
    previous_value_sha256: Digest
    proposed: ScalarConstant


class FutureCampaignDraft(WireModel):
    kind: Literal['future_campaign']
    title: Annotated[str, Field(min_length=1, max_length=128)]
    definition: ExecutableCampaignV4
    expected_evidence: Annotated[tuple[CampaignEvidenceIntent, ...], Field(max_length=64)]


class CampaignAdjustmentDraft(WireModel):
    kind: Literal['declared_adjustment']
    cut: GraphReadCut
    changes: Annotated[tuple[CampaignInputAdjustment, ...], Field(min_length=1, max_length=64)]
    expected_evidence: Annotated[tuple[CampaignEvidenceIntent, ...], Field(max_length=64)]


CampaignCandidateDraft = Annotated[FutureCampaignDraft | CampaignAdjustmentDraft, Field(discriminator='kind')]


class CampaignAlternative(WireModel):
    candidate_id: Identifier
    descriptor_sha256: Digest | None
    description: Description
    reason: Description


class CampaignUnresolvedPoint(WireModel):
    question: ResearchQuestionRef | None
    need: EvidenceNeedRef | None
    posture: Literal['unknown', 'weak', 'contradictory', 'missing', 'inapplicable']
    description: Description


class CampaignDraft(WireModel):
    schema_version: Literal['1'] = '1'
    authority: Literal['proposal_only']
    scientific_authority: Literal['not_established']
    action: Literal['abstain', 'request_evidence', 'propose_campaign']
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]
    decision_scope: Digest
    candidate: CampaignCandidateDraft | None
    evidence_requests: Annotated[tuple[CampaignEvidenceIntent, ...], Field(max_length=64)]
    alternatives: Annotated[tuple[CampaignAlternative, ...], Field(max_length=16)]
    unresolved: Annotated[tuple[CampaignUnresolvedPoint, ...], Field(max_length=64)]


def campaign_draft_schema() -> SchemaRef:
    schema = CampaignDraft.model_json_schema(mode='validation')
    schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    schema['$id'] = 'urn:amphora:planning.campaign-draft:1:validation'
    raw = (json.dumps(schema, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    return SchemaRef(schema_id='planning.campaign-draft', version='1', sha256=hashlib.sha256(raw).hexdigest())
