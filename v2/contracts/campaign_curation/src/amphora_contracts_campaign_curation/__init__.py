"""Additive campaign-curation contracts; no scheduling or owner authority."""
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError, NUMERIC_ENCODING

from .models import (
    CapabilityFulfillmentReceipt, CapabilityFulfillmentRequest, CapabilityFulfillmentSpecification,
    CapabilityRequestRef, CapabilityRequestView, CurationContext, CurationPhase, CurationProviderRecord,
    CurationReceipt, CurationReceiptQuery, CurationRef, CurationRequest, CurationSpecification, CurationView,
)
from .output import (
    CampaignCurationDraft, CapabilityGap, CurationAbstention, CurationCapabilityRequest,
    CurationProposal, RequestedCapabilityPort, campaign_curation_draft_schema,
)


def parse_curation(raw: str | bytes) -> CanonicalCommand:
    command = CanonicalCommand.for_family(raw, 'planning.curate_campaign',
                                          CurationSpecification, allow_numeric=True)
    if command.profile != NUMERIC_ENCODING:
        raise CommandEncodingError('curation_encoding_required')
    # Relationship validation is deliberately separate from transport construction.
    request = CurationRequest.model_validate_json(command.canonical_bytes)
    context = request.payload.context
    scopes = [context.draft.scope]
    scopes += [head.snapshot.graph.scope for head in context.knowledge]
    scopes += [head.change.graph.scope for head in context.knowledge]
    scopes += [item.scope for item in (*context.questions, *context.needs, *context.artifacts)]
    if any(scope != command.identity.scope for scope in scopes):
        raise CommandEncodingError('curation_scope_mismatch')
    if any(head.snapshot.graph != head.change.graph for head in context.knowledge):
        raise CommandEncodingError('curation_knowledge_graph_mismatch')
    if not request.payload.direction.strip():
        raise CommandEncodingError('curation_empty_direction')
    return command


def parse_fulfillment(raw: str | bytes) -> CanonicalCommand:
    command = CanonicalCommand.for_family(raw, 'planning.fulfill_capability',
                                          CapabilityFulfillmentSpecification, allow_numeric=True)
    if command.profile != NUMERIC_ENCODING:
        raise CommandEncodingError('fulfillment_encoding_required')
    request = CapabilityFulfillmentRequest.model_validate_json(command.canonical_bytes)
    scopes = [request.payload.request.scope, *(item.scope for item in request.payload.acceptance_evidence)]
    if any(scope != command.identity.scope for scope in scopes):
        raise CommandEncodingError('fulfillment_scope_mismatch')
    return command


__all__ = [
    'CapabilityFulfillmentReceipt', 'CapabilityFulfillmentRequest', 'CapabilityFulfillmentSpecification',
    'CapabilityRequestRef', 'CapabilityRequestView', 'CurationContext', 'CurationPhase',
    'CurationProviderRecord', 'CurationReceipt', 'CurationReceiptQuery', 'CurationRef', 'CurationRequest',
    'CurationSpecification', 'CurationView', 'CampaignCurationDraft', 'CapabilityGap', 'CurationAbstention',
    'CurationCapabilityRequest', 'CurationProposal', 'RequestedCapabilityPort',
    'campaign_curation_draft_schema', 'parse_curation', 'parse_fulfillment',
]
