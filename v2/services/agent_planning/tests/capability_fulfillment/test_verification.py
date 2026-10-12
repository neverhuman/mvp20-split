from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from threading import Barrier

import pytest
from sqlalchemy import text

from amphora_agent_planning.capability_acceptance.review import AcceptanceRejected, AcceptanceReview
from amphora_agent_planning.capability_fulfillment.journal import FulfillmentJournal
from amphora_agent_planning.capability_fulfillment.verification import FulfillmentVerifier, lookup
from amphora_agent_planning.capability_fulfillment.original import OriginalFulfillment
from amphora_agent_planning.capability_requests.projection import CurationCapabilities
from amphora_agent_planning.capability_requests.reader import CapabilityRequestReader
from amphora_agent_planning.curation_intake.commands import FulfillmentCommand
from amphora_agent_planning.curation_result.journal import CurationResultJournal
from ..capability_acceptance.test_review import case, evidence
from ..curation_execution.test_executor import setup as execution

pytestmark = pytest.mark.postgres


class Collector:
    def __init__(self, release, processed):
        self.release, self.processed, self.calls = release, processed, 0

    def collect(self, capability, specification):
        self.calls += 1
        return AcceptanceReview.bind(capability, specification, self.release, self.processed)


def setup(stored):
    principal, lease, linked, executor, provider, _ = execution(stored)
    template, release, report = case()
    raw = json.loads(provider.raw)
    raw['outcome'] = {'kind': 'request_capabilities', 'gaps': [template.gap.model_dump(mode='json')]}
    provider.raw = json.dumps(raw).encode()
    executor.execute(principal, lease)
    progress = CurationResultJournal(stored.engine).record(principal, lease)
    capability = CurationCapabilities.bind(progress.view).requests[0]
    release = release.model_copy(update={'scope': principal.scope})
    report.update(request=capability.reference.model_dump(mode='json'), proposal_sha256=capability.proposal_sha256)
    spec, processed = evidence(capability, release, report)
    owner = replace(principal, actions=frozenset({'fulfill_capabilities', 'read_capabilities'}))
    worker = replace(principal, actions=frozenset({'execute_curations'}))
    raw = {'encoding': 'amphora-command-v2', 'identity': {'scope': principal.scope.model_dump(),
        'actor_id': principal.actor_id, 'command_id': 'fulfill-1', 'command_family': 'planning.fulfill_capability'},
        'payload': spec.model_dump(mode='json')}
    journal = FulfillmentJournal(stored.engine)
    first = journal.receive(owner, json.dumps(raw))
    identifier = FulfillmentCommand.restore(json.dumps(raw)).fulfillment_id
    return owner, worker, raw, first, identifier, Collector(release, processed)


def test_verified_history_recovers_without_peers_and_initial_receipt_never_changes(stored):
    owner, worker, raw, first, identifier, collector = setup(stored)
    reader = CapabilityRequestReader(stored.engine)
    assert reader.read(owner, first.specification.request.request_id).fulfillment == first
    verifier = FulfillmentVerifier(stored.engine, collector)
    result = verifier.verify(worker, identifier)
    assert result.status == 'verified' and collector.calls == 1
    assert FulfillmentVerifier(stored.engine, None).verify(worker, identifier) == result
    assert FulfillmentJournal(stored.engine).receive(owner, json.dumps(raw)) == first
    visible = reader.read(owner, first.specification.request.request_id)
    assert visible.status == 'fulfilled' and visible.fulfillment == result
    with stored.engine.connect() as conn:
        row = conn.execute(text('SELECT * FROM planning.capability_fulfillments WHERE project_id=:project'),
            {'project': owner.scope.project_id}).mappings().one()
        restored = lookup(conn, OriginalFulfillment.restore(row))
        assert restored.receipt == result and restored.witness is not None
        assert b'planning-capability-verification.v1' in restored.witness.canonical


def test_competing_commands_cannot_replace_first_verified_winner(stored):
    owner, worker, raw, first, identifier, collector = setup(stored)
    raw['identity']['command_id'] = 'fulfill-2'
    FulfillmentJournal(stored.engine).receive(owner, json.dumps(raw))
    second = FulfillmentCommand.restore(json.dumps(raw)).fulfillment_id
    barrier = Barrier(2)
    original = collector.collect
    def simultaneous(capability, spec):
        result = original(capability, spec)
        barrier.wait(timeout=10)
        return result
    collector.collect = simultaneous
    verifier = FulfillmentVerifier(stored.engine, collector)
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks = [pool.submit(verifier.verify, worker, item) for item in (identifier, second)]
        results = [task.result(timeout=20) for task in tasks]
    winner = next(item for item in results if item.status == 'verified')
    loser = next(item for item in results if item.status == 'rejected')
    assert loser.reason_code == 'capability_already_fulfilled'
    assert CapabilityRequestReader(stored.engine).read(owner, first.specification.request.request_id).fulfillment == winner
    for item, result in zip((identifier, second), results, strict=True):
        assert FulfillmentVerifier(stored.engine, None).verify(worker, item) == result


def test_known_rejection_is_retained_but_transport_failure_remains_pending(stored):
    owner, worker, raw, first, identifier, collector = setup(stored)
    def unavailable(*args): raise TimeoutError('no_response')
    original = collector.collect
    collector.collect = unavailable
    verifier = FulfillmentVerifier(stored.engine, collector)
    with pytest.raises(TimeoutError): verifier.verify(worker, identifier)
    reader = CapabilityRequestReader(stored.engine)
    assert reader.read(owner, first.specification.request.request_id).fulfillment == first
    def rejected(*args): raise AcceptanceRejected('capability_acceptance_unproven')
    collector.collect = rejected
    result = verifier.verify(worker, identifier)
    assert result.status == 'rejected' and result.reason_code == 'capability_acceptance_unproven'
    collector.collect = original
    assert verifier.verify(worker, identifier) == result
    assert reader.read(owner, first.specification.request.request_id).status == 'requested'


def test_verification_commit_failure_recovers_and_authority_is_distinct(stored, monkeypatch):
    owner, worker, raw, first, identifier, collector = setup(stored)
    verifier = FulfillmentVerifier(stored.engine, collector)
    for denied in (owner, replace(worker, actions=frozenset({'read_capabilities'}))):
        with pytest.raises(PermissionError): verifier.verify(denied, identifier)
    with pytest.raises(ValueError, match='fulfillment_original_not_found'):
        verifier.verify(replace(worker, actor_id='foreign'), identifier)
    insert = verifier._insert
    def interrupted(*args):
        insert(*args)
        raise RuntimeError('before_commit')
    monkeypatch.setattr(verifier, '_insert', interrupted)
    with pytest.raises(RuntimeError, match='before_commit'): verifier.verify(worker, identifier)
    assert CapabilityRequestReader(stored.engine).read(owner, first.specification.request.request_id).fulfillment == first
    monkeypatch.setattr(verifier, '_insert', insert)
    assert verifier.verify(worker, identifier).status == 'verified'
