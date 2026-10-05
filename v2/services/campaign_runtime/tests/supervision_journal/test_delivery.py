"""Real database leases, original receipt reconciliation and bounded delivery."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_journal import RequestFrame
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_contracts_supervision import (
    SupervisionCommandReceipt,
    parse_supervision_command,
)
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .test_storage import command, setup


def prepared(g):
    e, journal, frame, params = setup(g)
    journal.prepare(e.principal, frame, command(frame))
    e.principal = replace(e.principal, actions=e.principal.actions | {'supervise_dispatch'})
    return e, DeliveryJournal(journal), frame, params


def receipt(frame, status='recorded', operation='original-operation'):
    outgoing = parse_supervision_command('planning.supervision.request', command(frame))
    outcome = {'status': status, 'binding': {'identity': outgoing.identity.model_dump(mode='json'),
        'request_sha256': outgoing.sha256, 'operation_id': operation}}
    if status == 'recorded':
        outcome['committed'] = {'kind': 'request', 'object_id': frame.request.planning_request.reference.engagement_id,
            'revision': 1, 'content_sha256': frame.request_sha256}
    elif status == 'rejected':
        outcome['reason_code'] = 'fixture_denied'
    import json
    return SupervisionCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))


def claim(delivery, principal, frame, key='claim-1', seconds=60):
    return delivery.claim(principal, frame.request.reference, frame.request_sha256, event_id=key, seconds=seconds)


def test_expired_holder_cannot_append_but_exact_replay_preserves_original_lease(graph_env):
    e, delivery, frame, _ = prepared(graph_env)
    first = claim(delivery, e.principal, frame, seconds=1)
    assert claim(delivery, e.principal, frame, seconds=1) == first
    assert claim(delivery, e.principal, frame, 'contender') is None
    with e.engine.connect() as conn:
        conn.execute(text('SELECT pg_sleep(1.05)'))
    second = claim(delivery, e.principal, frame, 'claim-2')
    assert second.fence == first.fence + 1
    assert claim(delivery, e.principal, frame, seconds=1) == first
    with pytest.raises(ValueError, match='delivery_lease_lost'):
        delivery.observe(e.principal, first, event_id='stale', reason='ambiguous_reply')
    saved = delivery.observe(e.principal, second, event_id='uncertain', reason='ambiguous_reply')
    assert saved.kind == 'unknown'
    assert delivery.observe(e.principal, second, event_id='uncertain', reason='ambiguous_reply') == saved
    with pytest.raises(ValueError, match='delivery_event_conflict'):
        delivery.observe(e.principal, second, event_id='uncertain', reason='different')


def test_pending_then_recorded_requires_exact_readback_and_original_operation(graph_env):
    e, delivery, frame, _ = prepared(graph_env)
    first = claim(delivery, e.principal, frame)
    delivery.observe(e.principal, first, event_id='pending', receipt=receipt(frame, 'pending'))
    second = claim(delivery, e.principal, frame, 'claim-2')
    with pytest.raises(ValueError, match='receipt_operation_changed'):
        delivery.observe(e.principal, second, event_id='wrong-operation', receipt=receipt(frame, operation='other'))
    event = delivery.observe(e.principal, second, event_id='committed', receipt=receipt(frame))
    assert event.kind == 'awaiting_readback'
    third = claim(delivery, e.principal, frame, 'claim-3')
    terminal = delivery.observe(e.principal, third, event_id='readback', receipt=receipt(frame), readback=frame.request)
    assert terminal.kind == 'recorded'
    assert claim(delivery, e.principal, frame, 'after-terminal') is None
    assert DeliveryJournal(delivery.requests).history(e.principal, frame.request.reference, frame.request_sha256)[-1] == terminal
    assert delivery.observe(e.principal, third, event_id='readback', receipt=receipt(frame), readback=frame.request) == terminal


def test_rejected_receipt_is_terminal_delivery_not_a_graph_decision(graph_env):
    e, delivery, frame, params = prepared(graph_env)
    lease = claim(delivery, e.principal, frame)
    assert delivery.observe(e.principal, lease, event_id='rejection', receipt=receipt(frame, 'rejected')).kind == 'rejected'
    assert claim(delivery, e.principal, frame, 'again') is None
    with e.engine.connect() as conn:
        assert conn.execute(text('SELECT status FROM runtime.runs WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run'), params).scalar_one() == 'running'


def test_unknown_delivery_keeps_one_command_and_stops_at_claim_limit(graph_env):
    e, delivery, frame, params = prepared(graph_env)
    for index in range(16):
        lease = claim(delivery, e.principal, frame, f'claim-{index}')
        delivery.observe(e.principal, lease, event_id=f'unknown-{index}', reason='network_uncertain')
    assert claim(delivery, e.principal, frame, 'exhausted') is None
    history = delivery.history(e.principal, frame.request.reference, frame.request_sha256)
    assert len(history) == 33 and history[-1].kind == 'failed'
    assert history[-1].evidence.reason == 'delivery_limit'
    assert claim(delivery, e.principal, frame, 'exhausted') is None
    assert delivery.requests.series(e.principal, params['run'], params['decision'])[0].canonical_command == command(frame)


def test_delivery_authority_and_immutable_grants(graph_env):
    e, delivery, frame, params = prepared(graph_env)
    with pytest.raises(ValueError, match='access_denied'):
        claim(delivery, replace(e.principal, actions=frozenset({'read'})), frame)
    with pytest.raises(ValueError, match='delivery_holder_mismatch'):
        claim(delivery, replace(e.principal, actor_id='other'), frame)
    with pytest.raises(ValueError, match='delivery_lease_seconds'):
        claim(delivery, e.principal, frame, seconds=301)
    claim(delivery, e.principal, frame)
    with pytest.raises(ValueError, match='delivery_event_conflict'):
        claim(delivery, e.principal, frame, seconds=5)
    for statement in ('DELETE FROM runtime.supervision_delivery_events',
                      'UPDATE runtime.supervision_delivery_events SET evidence=evidence',
                      'UPDATE runtime.supervision_delivery SET request_sha256=request_sha256'):
        with pytest.raises(DBAPIError), e.engine.begin() as conn:
            conn.execute(text(statement + ' WHERE tenant_id=:tenant AND project_id=:project'), params)


def test_lease_is_capped_by_original_request_deadline(graph_env):
    e, journal, frame, _ = setup(graph_env)
    with e.engine.connect() as conn:
        deadline = conn.execute(text('SELECT floor(extract(epoch from clock_timestamp())*1000)::bigint+1200')).scalar_one()
    request = frame.request.model_copy(update={'deadline_unix_ms': deadline})
    frame = RequestFrame.capture(request, frame.footprint(), prepared_by=e.principal.actor_id,
                                 planning_actor=request.planning_request.actor_id)
    journal.prepare(e.principal, frame, command(frame))
    e.principal = replace(e.principal, actions=e.principal.actions | {'supervise_dispatch'})
    delivery = DeliveryJournal(journal)
    lease = claim(delivery, e.principal, frame, seconds=300)
    assert round(lease.expires_at.timestamp() * 1000) == deadline
    with e.engine.connect() as conn:
        conn.execute(text('SELECT pg_sleep(1.25)'))
    with pytest.raises(ValueError, match='delivery_lease_lost'):
        delivery.observe(e.principal, lease, event_id='late', reason='uncertain')
    assert claim(delivery, e.principal, frame, 'expired') is None
    assert delivery.history(e.principal, frame.request.reference, frame.request_sha256)[-1].kind == 'expired'


def test_claim_without_receipt_can_expire_and_reconcile_unchanged_identity(graph_env):
    e, delivery, frame, _ = prepared(graph_env)
    first = claim(delivery, e.principal, frame, seconds=1)
    with e.engine.connect() as conn:
        conn.execute(text('SELECT pg_sleep(1.05)'))
    second = claim(delivery, e.principal, frame, 'recovery')
    assert second.fence > first.fence
    assert delivery.observe(e.principal, second, event_id='found-original', receipt=receipt(frame),
                            readback=frame.request).kind == 'recorded'
