from datetime import datetime, timezone
import json

import pytest
from amphora_contracts_campaign_curation import CampaignCurationDraft, CurationProviderRecord
from amphora_contracts_planning import ProviderUsage
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.curation_intake.record import OriginalCuration
from amphora_agent_planning.capability_requests.projection import CapabilityAddress, CurationCapabilities
from ..curation_context.test_intent import source
from ..curation_output.test_output import output


def view(kind='request_capabilities'):
    _, intent, incoming = source()
    original = OriginalCuration(incoming, datetime.now(timezone.utc)).view()
    raw = output(kind)
    raw['decision_scope'] = intent.request.document().decision_scope
    provider = CurationProviderRecord(attempt=AttemptBinding(intent.request, 1).reference(),
        envelope_sha256='a' * 64, output_sha256='b' * 64,
        usage=ProviderUsage(input_tokens=1, output_tokens=1, accounting_units=1, certainty='reported'),
        reservation_units=250000000)
    return original.model_copy(update={'provider': provider, 'proposal': CampaignCurationDraft.model_validate_json(json.dumps(raw))})


@pytest.mark.parametrize('kind', ['request_capabilities', 'propose_campaign'])
def test_stable_gap_views_do_not_modify_original_proposal_or_receipt(kind):
    original = view(kind)
    before = original.model_dump_json()
    enriched = CurationCapabilities.enrich(original)
    reference = enriched.capability_requests[0]
    address = CapabilityAddress.parse(reference.request_id)
    projected = CurationCapabilities.bind(enriched).at(address).view()
    assert projected.curation == original.receipt.reference
    assert projected.gap == original.proposal.outcome.gaps[0]
    assert projected.status == 'requested' and projected.fulfillment is None
    assert enriched.receipt == original.receipt and enriched.proposal == original.proposal
    assert CurationCapabilities.enrich(enriched) == enriched and original.model_dump_json() == before
    assert address.curation_id == original.receipt.reference.curation_id
    assert CurationCapabilities.bind(original).at(CapabilityAddress(address.curation_id, 15)) is None


def test_abstention_and_original_queued_intent_have_no_manufactured_requests():
    original = view('abstain')
    assert CurationCapabilities.bind(original).requests == ()
    assert CurationCapabilities.bind(original.model_copy(update={'provider': None, 'proposal': None})).references == ()


@pytest.mark.parametrize('fault', ['capture', 'ordinal', 'engagement', 'duplicate', 'references'])
def test_unbound_or_ambiguous_original_rejects(fault):
    original = view()
    if fault == 'capture': original = original.model_copy(update={'provider': None})
    if fault == 'ordinal': original = original.model_copy(update={'provider': original.provider.model_copy(update={
        'attempt': original.provider.attempt.model_copy(update={'ordinal': 2})})})
    if fault == 'engagement': original = original.model_copy(update={'provider': original.provider.model_copy(update={
        'attempt': original.provider.attempt.model_copy(update={'engagement': original.provider.attempt.engagement.model_copy(update={'engagement_id': 'foreign'})})})})
    if fault == 'duplicate': original = original.model_copy(update={'proposal': original.proposal.model_copy(update={
        'outcome': original.proposal.outcome.model_copy(update={'gaps': original.proposal.outcome.gaps * 2})})})
    if fault == 'references':
        ref = CurationCapabilities.bind(original).references[0].model_copy(update={'request_id': 'foreign'})
        original = original.model_copy(update={'capability_requests': (ref,)})
    with pytest.raises(ValueError): CurationCapabilities.bind(original)


@pytest.mark.parametrize('value', ['capability-' + 'a' * 64 + '-16', 'capability-' + 'a' * 64 + '-0',
    'capability-' + 'a' * 64 + '-00\n', 'missing', '', None])
def test_unknown_address_never_aliases_an_original_gap(value):
    assert CapabilityAddress.parse(value) is None
