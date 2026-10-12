import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from amphora_agent_planning.capability_fulfillment.failures import rejection, retryable
from amphora_agent_planning.capability_fulfillment.journal import FulfillmentJournal
from amphora_agent_planning.capability_fulfillment.verification import FulfillmentVerifier
from amphora_agent_planning.capability_fulfillment.worker import FulfillmentWorker
from amphora_agent_planning.curation_worker.polling import CurationPoller
from .test_verification import setup


@pytest.mark.parametrize('reason', ['source_access_denied', 'source_reference_unavailable', 'metadata_denied',
    'metadata_missing', 'registry_scope', 'registry_lock', 'registry_duplicate_port'])
def test_known_denial_and_descriptor_mismatch_are_rejections(reason):
    assert rejection(ValueError(reason)) == reason
    assert not retryable(ValueError(reason))


@pytest.mark.parametrize('reason', ['metadata_unavailable', 'metadata_protocol', 'metadata_media', 'metadata_deadline'])
def test_transient_public_metadata_failure_remains_pending(reason):
    assert rejection(ValueError(reason)) is None and retryable(ValueError(reason))


def test_unknown_integrity_failures_are_not_disguised_as_peer_outage():
    assert rejection(ValueError('stored_fulfillment_witness_mismatch')) is None
    assert not retryable(ValueError('stored_fulfillment_witness_mismatch'))


@pytest.mark.postgres
def test_pending_discovery_advances_and_terminal_records_are_excluded(stored):
    owner, principal, raw, first, identifier, collector = setup(stored)
    raw['identity']['command_id'] = 'second'
    FulfillmentJournal(stored.engine).receive(owner, json.dumps(raw))
    worker = FulfillmentWorker(FulfillmentVerifier(stored.engine, collector))
    collect = collector.collect
    def pending(*args): raise TimeoutError()
    collector.collect = pending
    one, two = worker.tick(principal), worker.tick(principal)
    assert one.status == two.status == 'fulfillment_pending' and one.fulfillment_id != two.fulfillment_id
    collector.collect = collect
    outcomes = [worker.tick(principal), worker.tick(principal)]
    assert {item.status for item in outcomes} == {'fulfillment_verified', 'fulfillment_rejected'}
    assert worker.tick(principal) is None
    assert FulfillmentWorker(worker.verifier).tick(principal) is None
    assert FulfillmentWorker(worker.verifier).tick(replace(principal, actor_id='foreign')) is None
    with pytest.raises(PermissionError): worker.tick(owner)


def test_fulfillment_pending_cannot_starve_campaign_turns():
    poller = CurationPoller(SimpleNamespace(engine=None, tick=lambda *args: 'campaign'), ['synthetic'], 'worker',
        fulfillments=SimpleNamespace(tick=lambda principal: 'fulfillment'))
    poller.discovery = SimpleNamespace(next=lambda principal: 'curation')
    assert [poller.tick(None) for _ in range(4)] == ['fulfillment', 'campaign', 'fulfillment', 'campaign']
    poller.fulfillments.tick = lambda principal: None
    assert poller.tick(None) == 'campaign'
    poller.discovery.next = lambda principal: None
    poller.fulfillments.tick = lambda principal: 'fulfillment'
    assert poller.tick(None) == 'fulfillment'
