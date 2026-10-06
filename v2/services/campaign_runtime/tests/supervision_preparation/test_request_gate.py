"""Actual SQL atomicity, replay, contention and original recipe enforcement."""

import copy
import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.supervision_journal.checkpoint_frames import (
    CheckpointFrame,
)
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_campaign_runtime.supervision_preparation.catalog import RecipeCatalog
from amphora_campaign_runtime.supervision_preparation.request_gate import (
    RequestReservation,
)
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_requests.projection import CheckpointExport
from amphora_contracts_planning import checkpoint_draft_schema
from amphora_contracts_supervision import CheckpointRequest, parse_checkpoint_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_checkpoints.test_coordinator import slots
from ..supervision_journal.test_checkpoint_frames import frame as literal_frame
from ..supervision_journal.test_checkpoint_storage import command as original_outgoing
from ..supervision_policy.test_admission import command
from .test_policy_pins import configuration, service


def outgoing(frame):
    raw = json.loads(original_outgoing(frame).canonical_bytes)
    raw['identity']['command_id'] = frame.request_sha256
    return parse_checkpoint_command(json.dumps(raw))


def setup(graph, *, calls=1):
    actor = replace(graph.env.principal, actions=graph.env.principal.actions | {'supervise_prepare', 'read'})
    graph.env.principal = actor
    recipe, policy = configuration(graph)
    record = policy.document().model_dump(mode='json')
    record['checkpoints'][0].update(max_requests=2, max_model_calls=calls, timeout_seconds=300)
    policy = ReviewedPolicy.bind(policy.plan, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    receipt = service(graph, policy, RecipeCatalog([recipe])).admit_supervised(actor, command(graph, policy))
    run = receipt.outcome.committed.object_id
    slot = slots(graph, run, policy)[0]
    data = literal_frame().request.model_dump(mode='json')

    def rescope(item):
        if isinstance(item, dict):
            if set(item) == {'tenant_id', 'project_id'}:
                item.update(actor.scope.model_dump(mode='json'))
            for value in item.values():
                rescope(value)
        elif isinstance(item, list):
            for value in item:
                rescope(value)

    rescope(data)
    data['reference'].update(run_id=run, decision_id=slot.seed.decision_id)
    data.update(checkpoint_id=slot.seed.document().checkpoint_id,
                snapshot=CheckpointExport(slot.seed.footprint()).document().model_dump(mode='json'),
                deadline_unix_ms=int(slot.deadline.timestamp() * 1000))
    data['policy']['sha256'] = policy.sha256
    original = data['planning_request']
    original['runtime_cut'] = slot.seed.footprint().cut.model_dump(mode='json')
    context = recipe.document().model_dump(mode='json')
    context.pop('profile')
    context.pop('budget_policy')
    context.update(schema_version='1', policy=data['policy'], output_schema=checkpoint_draft_schema().model_dump(mode='json'))
    declaration = dict(data['policy'], artifact_id='declaration', sha256=original['decision_scope'])
    context['entries'].append({'artifact': declaration, 'role': 'constraint', 'required': True})
    original['context'] = context
    journal = RequestJournal(graph.env.engine, {(actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'})
    return actor, slot, data, journal


def frame(data, slot, actor):
    request = CheckpointRequest.model_validate_json(json.dumps(data))
    data = copy.deepcopy(data)
    data['planning_request_sha256'] = hashlib.sha256(encoded(request.planning_request)).hexdigest()
    return CheckpointFrame.capture(CheckpointRequest.model_validate_json(json.dumps(data)), slot.seed.footprint(),
                                   prepared_by=actor.actor_id, planning_actor='fixture')


def counts(graph, run):
    with graph.env.engine.connect() as conn:
        return tuple(conn.execute(text(f'SELECT count(*) FROM runtime.{table} WHERE run_id=:run'),
                                  {'run': run}).scalar_one() for table in
                     ['supervision_requests', 'supervision_outbox', 'supervision_call_reservations'])


def test_atomic_reservation_exact_replay_and_no_refund_after_cancel(graph_env):
    graph = graph_env
    actor, slot, data, journal = setup(graph)
    request = frame(data, slot, actor)
    stored = journal.prepare(actor, request, outgoing(request).canonical_bytes)
    run = request.request.reference.run_id
    assert counts(graph, run) == (1, 1, 1)
    with graph.env.engine.begin() as conn:
        assert conn.execute(text('SELECT max_attempts FROM runtime.supervision_call_reservations WHERE run_id=:run'),
                            {'run': run}).scalar_one() == 1
        for sql in ['UPDATE runtime.supervision_call_reservations SET max_attempts=1',
                    'DELETE FROM runtime.supervision_call_reservations']:
            with pytest.raises(DBAPIError), conn.begin_nested():
                conn.execute(text(sql))
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': run})
    assert journal.prepare(actor, request, outgoing(request).canonical_bytes) == stored
    assert counts(graph, run) == (1, 1, 1)


def test_failed_reservation_rolls_back_request_and_outbox(graph_env, monkeypatch):
    graph = graph_env
    actor, slot, data, journal = setup(graph)
    request = frame(data, slot, actor)
    persist = RequestReservation.persist

    def fail(*args):
        persist(*args)
        raise RuntimeError('reservation-abort')

    monkeypatch.setattr(RequestReservation, 'persist', fail)
    with pytest.raises(RuntimeError, match='reservation-abort'):
        journal.prepare(actor, request, outgoing(request).canonical_bytes)
    assert counts(graph, request.request.reference.run_id) == (0, 0, 0)
    monkeypatch.setattr(RequestReservation, 'persist', persist)
    journal.prepare(actor, request, outgoing(request).canonical_bytes)
    assert counts(graph, request.request.reference.run_id) == (1, 1, 1)


def test_repair_cannot_exceed_original_physical_call_allowance(graph_env):
    actor, slot, data, journal = setup(graph_env)
    first = frame(data, slot, actor)
    journal.prepare(actor, first, outgoing(first).canonical_bytes)
    data['lineage'] = {'ordinal': 2, 'root_request_sha256': first.request_sha256, 'parent_request_sha256': first.request_sha256}
    data['planning_request']['reference']['engagement_id'] = uuid.uuid4().hex
    second = frame(data, slot, actor)
    with pytest.raises(ValueError, match='reservation_slot_calls'):
        journal.prepare(actor, second, outgoing(second).canonical_bytes)
    assert counts(graph_env, first.request.reference.run_id) == (1, 1, 1)


@pytest.mark.parametrize('case,reason', [
    ('model', 'recipe_context_binding'), ('limits', 'recipe_limits_widened'),
    ('static', 'recipe_static_context'), ('declaration', 'recipe_declaration_context'),
    ('policy', 'reservation_policy_binding'), ('checkpoint', 'reservation_checkpoint_binding'),
    ('deadline', 'reservation_checkpoint_deadline'),
    ('alias', 'recipe_declaration_identity'),
])
def test_original_configuration_cannot_be_bypassed(graph_env, case, reason):
    actor, slot, data, journal = setup(graph_env)
    context = data['planning_request']['context']
    if case == 'model':
        context['model']['model_revision'] = 'changed'
    elif case == 'limits':
        context['limits']['max_attempts'] = 2
    elif case == 'static':
        context['entries'].pop(0)
    elif case == 'declaration':
        context['entries'][-1]['required'] = False
    elif case == 'policy':
        data['policy']['sha256'] = 'f' * 64
    elif case == 'checkpoint':
        data['checkpoint_id'] = 'not-the-pinned-checkpoint'
    elif case == 'alias':
        context['entries'][-1]['artifact']['artifact_id'] = context['objective']['artifact_id']
    else:
        data['deadline_unix_ms'] += 1
    request = frame(data, slot, actor)
    with pytest.raises(ValueError, match=reason):
        journal.prepare(actor, request, outgoing(request).canonical_bytes)
    assert counts(graph_env, request.request.reference.run_id) == (0, 0, 0)


def test_competing_preparers_reserve_only_one_original_request(graph_env):
    actor, slot, data, journal = setup(graph_env)
    first = frame(data, slot, actor)
    data['planning_request']['reference']['engagement_id'] = uuid.uuid4().hex
    second = frame(data, slot, actor)
    barrier = Barrier(2)

    def submit(request):
        barrier.wait(timeout=10)
        try:
            return journal.prepare(actor, request, outgoing(request).canonical_bytes)
        except ValueError as error:
            assert str(error) == 'request_identity_conflict'
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, [first, second]))
    assert sum(item is not None for item in results) == 1
    assert counts(graph_env, first.request.reference.run_id) == (1, 1, 1)


@pytest.mark.parametrize('missing', [False, True])
def test_distinct_repairs_reserve_again_and_unaccounted_history_fails_closed(graph_env, monkeypatch, missing):
    actor, slot, data, journal = setup(graph_env, calls=2)
    first = frame(data, slot, actor)
    persist = RequestReservation.persist
    if missing:
        monkeypatch.setattr(RequestReservation, 'persist', lambda *args: None)
    journal.prepare(actor, first, outgoing(first).canonical_bytes)
    monkeypatch.setattr(RequestReservation, 'persist', persist)
    data['lineage'] = {'ordinal': 2, 'root_request_sha256': first.request_sha256, 'parent_request_sha256': first.request_sha256}
    data['planning_request']['reference']['engagement_id'] = uuid.uuid4().hex
    second = frame(data, slot, actor)
    if missing:
        with pytest.raises(ValueError, match='reservation_history_incomplete'):
            journal.prepare(actor, second, outgoing(second).canonical_bytes)
        assert counts(graph_env, first.request.reference.run_id) == (1, 1, 0)
    else:
        stored = journal.prepare(actor, second, outgoing(second).canonical_bytes)
        assert journal.prepare(actor, second, outgoing(second).canonical_bytes) == stored
        assert counts(graph_env, first.request.reference.run_id) == (2, 2, 2)
