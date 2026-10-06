"""Actual SQL issuance cannot extend the original checkpoint call window."""

from datetime import datetime, timedelta, timezone

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.providers import FixtureProvider, observe
from amphora_agent_planning.supervision_intake import SupervisionIntake
from sqlalchemy import text

from ..persistence.test_dispatch import expire, prepare
from ..supervision_intake.test_checkpoints import command, request

pytestmark = pytest.mark.postgres


def checkpoint(s, offset_ms):
    with s.engine.connect() as conn:
        now = conn.execute(text('SELECT floor(extract(epoch FROM clock_timestamp())*1000)::bigint')).scalar_one()
    value = request(s.principal).model_copy(update={'deadline_unix_ms': now + offset_ms})
    intake = SupervisionIntake(s.engine)
    assert intake.receive(s.principal, command(value)).outcome.status == 'recorded'
    s.snapshot = intake.request(s.principal, value.planning_request.reference.engagement_id).planning
    s.first, s.second = AttemptBinding(s.snapshot, 1), AttemptBinding(s.snapshot, 2)
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=now + offset_ms)


def test_expired_checkpoint_never_issues_or_calls(stored):
    s = stored
    checkpoint(s, -1)
    dispatch, _, _, policy = prepare(s)
    with pytest.raises(ValueError, match='checkpoint_deadline'):
        dispatch.issue(s.principal, s.first, 86400)
    class Forbidden:
        def supports(self, model):
            raise AssertionError('expired checkpoint reached provider')
    result = PlanningRunner(s.engine, Forbidden(), timeout_seconds=10).run(s.principal, s.snapshot, policy)
    assert result.stop_reason == 'checkpoint_deadline' and result.attempts == ()
    with s.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.dispatches WHERE project_id=:project'),
                            {'project': s.principal.scope.project_id}).scalar_one() == 0


def test_absolute_deadline_caps_timeout_and_replacement_recovers_original(stored):
    s = stored
    deadline = checkpoint(s, 1800)
    dispatch, _, settlements, policy = prepare(s)
    ticket = dispatch.issue(s.principal, s.first, 86400)
    assert ticket.deadline == deadline
    expire(s, ticket)
    assert dispatch.issue(s.principal, s.first, 86400) is None
    recovered = dispatch.recover(s.principal, s.first)
    assert recovered.observation.document().reason_code == 'attempt_deadline'
    original = settlements.settle(s.principal, s.first)
    late = observe(s.first, FixtureProvider('abstain'))
    assert dispatch.complete(s.principal, s.first, ticket, late) == recovered
    assert dispatch.read_late(s.principal, s.first) == late
    runner = PlanningRunner(s.engine, FixtureProvider('abstain'), timeout_seconds=86400)
    result = runner.run(s.principal, s.snapshot, policy)
    assert result.stop_reason == 'checkpoint_deadline' and len(result.attempts) == 1
    assert settlements.read(s.principal, s.first.reference()) == original


def test_shorter_dispatch_timeout_is_not_extended(stored):
    s = stored
    deadline = checkpoint(s, 60000)
    dispatch, _, _, _ = prepare(s)
    ticket = dispatch.issue(s.principal, s.first, 1)
    assert ticket.deadline < deadline
