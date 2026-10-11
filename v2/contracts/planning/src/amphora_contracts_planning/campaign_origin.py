"""Historical compiler provenance; no execution or scientific authority."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SafePositiveInt, Scope, WireModel
from amphora_contracts_graph_runtime import DraftCommandReceipt
from amphora_contracts_research import EvidenceAssessmentRequest, EvidenceNeedRef, ResearchQuestionRef
from amphora_contracts_tools import LockEntry
from pydantic import Field

from .campaign_context import CampaignResearchSelection
from .campaign_output import CampaignNodeAddress
from .context import ContextManifest
from .engagement import ProviderAttemptRef, ProviderUsage
from .followup import CampaignFollowupSelection, _profile


class CampaignOriginDraft(WireModel):
    scope: Scope
    draft_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest


class CampaignOriginProposal(WireModel):
    actor_id: Identifier
    attempt: ProviderAttemptRef
    preparation_sha256: Digest
    prepared_proposal_sha256: Digest
    output_sha256: Digest
    action: Literal['propose_campaign']
    rationale: Annotated[str, Field(min_length=1, max_length=4096)]
    context: ContextManifest
    usage: ProviderUsage
    capture_publication: Literal['not_published']


class CampaignOriginSave(WireModel):
    owner_id: Identifier
    selection_id: Identifier
    selection_sha256: Digest
    effect_id: Identifier
    effect_sha256: Digest
    receipt: DraftCommandReceipt
    readback_sha256: Digest


class CampaignOriginResearchRecord(WireModel):
    kind: Literal['question', 'need', 'assessment']
    reference: ResearchQuestionRef | EvidenceNeedRef | EvidenceAssessmentRequest
    record_sha256: Digest | None
    unavailable: Literal['not_provided', 'unavailable', 'denied', 'pending', 'failed'] | None
    # Criteria present in consumed question/need metadata, not inferred model intent.
    criterion_ids: Annotated[tuple[Identifier, ...], Field(max_length=32)]


class CampaignOriginResearch(WireModel):
    selection: Annotated[CampaignResearchSelection | CampaignFollowupSelection,
                         Field(discriminator='schema_version')] | None
    records: Annotated[tuple[CampaignOriginResearchRecord, ...], Field(max_length=160)]


class CampaignOriginTool(WireModel):
    node: CampaignNodeAddress
    release: LockEntry


class CampaignOriginBody(WireModel):
    schema_version: Literal['1'] = '1'
    authority: Literal['historical_compiler_provenance']
    draft: CampaignOriginDraft
    proposal: CampaignOriginProposal
    save: CampaignOriginSave
    research: CampaignOriginResearch
    tools: Annotated[tuple[CampaignOriginTool, ...], Field(max_length=4096)]
    limitations: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=16)]


class CampaignOrigin(WireModel):
    schema_version: Literal['1'] = '1'
    origin_sha256: Digest
    origin: CampaignOriginBody


def campaign_origin_schema():
    return _profile(CampaignOrigin, 'planning.campaign-origin')
