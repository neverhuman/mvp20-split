"""Real Planning SQL intake preserves history without provider effects."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.supervision_intake import SupervisionIntake
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .support import command, request


def test_atomic_wrapper_legacy_request_and_original_receipt(stored):
    e = stored
    intake = SupervisionIntake(e.engine)
    value = request(e.principal)
    incoming = command(value)
    first = intake.receive(e.principal, incoming)
    assert first.outcome.status == 'recorded'
    replacement = SupervisionIntake(e.engine)
    assert replacement.receive(e.principal, incoming) == first
    readonly = replace(e.principal, actions=frozenset({'read_attempts'}))
    assert replacement.receipt(readonly, 'command-1') == first
    observed = replacement.request(readonly, value.planning_request.reference.engagement_id)
    assert observed.document() == value
    assert e.journal.read_request(readonly, value.planning_request.reference) == observed.planning
    second_ack = intake.receive(e.principal, command(value, 'second-acknowledgment'))
    assert second_ack.outcome.committed == first.outcome.committed
    assert second_ack.outcome.binding.operation_id != first.outcome.binding.operation_id
    assert intake.request(readonly, value.planning_request.reference.engagement_id) == observed
    assert replacement.request(readonly, 'missing') is None and replacement.receipt(readonly, 'missing') is None
    with e.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': e.principal.scope.tenant_id, 'project': e.principal.scope.project_id}).scalar_one() == 0
    with pytest.raises(PermissionError, match='planning_access_denied'):
        replacement.receive(readonly, incoming)


def test_rollback_does_not_leave_half_an_intake(stored, monkeypatch):
    e = stored
    intake = SupervisionIntake(e.engine)
    value = request(e.principal)
    incoming = command(value)
    original = intake._record_command
    def fail(*args):
        raise RuntimeError('wrapper_before_receipt')
    monkeypatch.setattr(intake, '_record_command', fail)
    with pytest.raises(RuntimeError, match='wrapper_before_receipt'):
        intake.receive(e.principal, incoming)
    assert intake.request(e.principal, value.planning_request.reference.engagement_id) is None
    assert intake.receipt(e.principal, 'command-1') is None
    assert e.journal.read_request(e.principal, value.planning_request.reference) is None
    monkeypatch.setattr(intake, '_record_command', original)
    assert intake.receive(e.principal, incoming).outcome.status == 'recorded'


def test_preexisting_legacy_request_and_changed_wrappers(stored):
    e = stored
    intake = SupervisionIntake(e.engine)
    value = request(e.principal)
    original = RequestSnapshot.bind(value.planning_request, actor_id=e.principal.actor_id, scope=e.principal.scope)
    e.journal.register(e.principal, original)
    intake.receive(e.principal, command(value))
    changed = value.model_copy(update={'checkpoint_id': 'different'})
    with pytest.raises(ValueError, match='supervision_command_conflict'):
        intake.receive(e.principal, command(changed))
    denied = intake.receive(e.principal, command(changed, 'new-command'))
    assert denied.outcome.reason_code == 'supervision_request_conflict'
    assert intake.receipt(e.principal, 'new-command') == denied
    changed = request(e.principal, lambda d: d['planning_request']['context']['limits'].update(total_tokens=5000))
    denied = intake.receive(e.principal, command(changed, 'different-planning'))
    assert denied.outcome.reason_code == 'planning_request_conflict'
    assert intake.receipt(e.principal, 'different-planning') == denied
    assert e.journal.read_request(e.principal, value.planning_request.reference) == original


def test_scoped_reads_and_insert_only_grants(stored):
    e = stored
    intake = SupervisionIntake(e.engine)
    value = request(e.principal)
    intake.receive(e.principal, command(value))
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={'project_id': 'foreign'}))
    assert intake.request(foreign, value.planning_request.reference.engagement_id) is None
    assert intake.receipt(foreign, 'command-1') is None
    with pytest.raises(ValueError, match='actor_mismatch'):
        intake.request(replace(e.principal, actor_id='other'), value.planning_request.reference.engagement_id)
    for table in ('supervision_requests', 'supervision_commands'):
        for verb in ('DELETE FROM', 'UPDATE'):
            statement = f'{verb} planning.{table}' + (' SET recorded_at=clock_timestamp()' if verb == 'UPDATE' else '')
            with pytest.raises(DBAPIError), e.engine.begin() as conn:
                conn.execute(text(statement + ' WHERE tenant_id=:tenant AND project_id=:project'),
                    {'tenant': e.principal.scope.tenant_id, 'project': e.principal.scope.project_id})


@pytest.mark.parametrize('conflict', [False, True])
def test_competing_exact_commands_or_slot_identities(stored, conflict):
    e = stored
    intake = SupervisionIntake(e.engine)
    barrier = Barrier(2)
    def receive(index):
        def change(data):
            if conflict:
                data['planning_request']['reference']['engagement_id'] = f'engagement-{index}'
        value = request(e.principal, change)
        incoming = command(value, f'command-{index}' if conflict else 'command-1')
        barrier.wait(timeout=5)
        return intake.receive(e.principal, incoming)
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = tuple(pool.map(receive, (0, 1)))
    if conflict:
        assert sorted((a.outcome.status, b.outcome.status)) == ['recorded', 'rejected']
    else:
        assert a == b
