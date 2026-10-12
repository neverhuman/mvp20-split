"""Transport pins only; Planning owns curation, authorization and state transitions."""
from typing import Annotated, Literal

from amphora_contracts_commands import CommandIdentity
from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from amphora_contracts_graph_runtime import DraftSelection, PredecessorCut
from amphora_contracts_knowledge import DomainHead
from amphora_contracts_planning import CampaignOriginDraft, ProviderAttemptRef, ProviderUsage
from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef
from amphora_contracts_tools import LockEntry
from pydantic import AwareDatetime, Field

from .output import CampaignCurationDraft, CapabilityGap


class CurationContext(WireModel):
    predecessor: PredecessorCut
    draft: CampaignOriginDraft
    knowledge: Annotated[tuple[DomainHead, ...], Field(max_length=8)]
    questions: Annotated[tuple[ResearchQuestionRef, ...], Field(max_length=32)]
    needs: Annotated[tuple[EvidenceNeedRef, ...], Field(max_length=32)]
    artifacts: Annotated[tuple[ArtifactRef, ...], Field(max_length=16)]


class CurationSpecification(WireModel):
    direction: Annotated[str, Field(min_length=1, max_length=4096)]
    policy_id: Identifier
    context: CurationContext


class CurationRequest(WireModel):
    encoding: Literal['amphora-command-v2']
    identity: CommandIdentity
    payload: CurationSpecification


class CurationRef(WireModel):
    scope: Scope
    curation_id: Identifier


class CurationReceiptQuery(WireModel):
    identity: CommandIdentity
    request_sha256: Digest


CurationPhase = Literal['queued', 'assembling', 'awaiting_provider', 'proposed', 'abstained',
                        'compiling', 'ready', 'failed', 'indeterminate']


class CurationReceipt(WireModel):
    wire_version: Literal['1'] = '1'
    identity: CommandIdentity
    request_sha256: Digest
    reference: CurationRef
    revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    phase: CurationPhase
    reason_code: Identifier | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class CurationProviderRecord(WireModel):
    attempt: ProviderAttemptRef
    envelope_sha256: Digest
    output_sha256: Digest | None
    usage: ProviderUsage
    reservation_units: Annotated[int, Field(ge=0, le=9007199254740991)]


class CapabilityRequestRef(WireModel):
    scope: Scope
    request_id: Identifier


class CurationView(WireModel):
    wire_version: Literal['1'] = '1'
    receipt: CurationReceipt
    specification: CurationSpecification
    provider: CurationProviderRecord | None
    proposal: CampaignCurationDraft | None
    capability_requests: Annotated[tuple[CapabilityRequestRef, ...], Field(max_length=16)]
    validated_draft: DraftSelection | None


class CapabilityFulfillmentSpecification(WireModel):
    request: CapabilityRequestRef
    release: LockEntry
    acceptance_evidence: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=16)]


class CapabilityFulfillmentRequest(WireModel):
    encoding: Literal['amphora-command-v2']
    identity: CommandIdentity
    payload: CapabilityFulfillmentSpecification


class CapabilityFulfillmentReceipt(WireModel):
    wire_version: Literal['1'] = '1'
    identity: CommandIdentity
    request_sha256: Digest
    specification: CapabilityFulfillmentSpecification
    status: Literal['pending', 'verified', 'rejected', 'indeterminate']
    reason_code: Identifier | None
    created_at: AwareDatetime


class CapabilityRequestView(WireModel):
    wire_version: Literal['1'] = '1'
    reference: CapabilityRequestRef
    curation: CurationRef
    proposal_sha256: Digest
    gap: CapabilityGap
    status: Literal['requested', 'fulfilled']
    fulfillment: CapabilityFulfillmentReceipt | None
