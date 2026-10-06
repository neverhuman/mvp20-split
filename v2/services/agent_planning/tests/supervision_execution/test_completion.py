"""Owner projection validates history without claiming SQL finalization."""

import hashlib
from dataclasses import replace

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.orchestration import RunOutcome
from amphora_agent_planning.persistence.records import AttemptJournal
from amphora_agent_planning.providers.capture import (
    CapturedOutput,
    Observation,
    unknown_usage,
)
from amphora_agent_planning.supervision_execution.completion import (
    STOP_REASONS,
    SUCCESS,
    ExecutionCompletion,
)
from amphora_agent_planning.supervision_intake.snapshot import encoded

from .test_context import prepared
from .test_worker import setup


def attempt(intake, ordinal=1, status='invalid'):
    binding = AttemptBinding(intake.planning, ordinal)
    observed = Observation.record(binding, CapturedOutput(b'bad', True), status, 'fixture', unknown_usage())
    return AttemptJournal(binding, observed)


@pytest.mark.parametrize('reason', sorted(STOP_REASONS - SUCCESS - {'attempt_limit'}))
def test_pre_call_stops_have_no_attempts_or_accounting(reason):
    actor, intake, *_ = prepared()
    result = ExecutionCompletion.bind(intake, actor, RunOutcome((), reason))
    wire = result.document()
    assert wire.attempts == () and wire.stop_reason == reason
    assert wire.request_sha256 == intake.sha256 and wire.planning_request_sha256 == intake.planning.sha256
    assert result.sha256 == hashlib.sha256(result.canonical).hexdigest()


def test_ordered_exhaustion_and_exact_observation_hash():
    actor, intake, *_ = prepared()
    maximum = intake.planning.document().context.limits.max_attempts
    history = tuple(attempt(intake, ordinal) for ordinal in range(1, maximum + 1))
    report = ExecutionCompletion.bind(intake, actor, RunOutcome(history, 'attempt_limit')).document()
    assert report.attempts[-1].observation_sha256 == hashlib.sha256(encoded(history[-1].observation.document())).hexdigest()
    with pytest.raises(ValueError, match='completion_not_exhausted'):
        ExecutionCompletion.bind(intake, actor, RunOutcome(history[:-1], 'attempt_limit'))
    with pytest.raises(ValueError, match='completion_attempt_limit'):
        ExecutionCompletion.bind(intake, actor, RunOutcome(history + history[:1], 'attempt_limit'))


@pytest.mark.parametrize('case,reason', [('pending', 'completion_attempt_pending'),
    ('ordinal', 'completion_attempt_identity'), ('status', 'completion_status_mismatch'),
    ('stop', 'completion_stop_reason'), ('corrupt', 'capture_digest_mismatch'),
    ('after_stop', 'completion_after_stop'), ('success_then_failure', 'completion_status_mismatch')])
def test_invalid_or_inflight_history_cannot_claim_completion(case, reason):
    actor, intake, *_ = prepared()
    item, stop = attempt(intake), 'required_artifact_unavailable'
    if case == 'pending':
        item = replace(item, observation=None)
    elif case == 'ordinal':
        item = attempt(intake, 2)
    elif case == 'status':
        stop = 'abstained'
    elif case == 'stop':
        stop = 'attempt_pending'
    elif case == 'corrupt':
        item = replace(item, observation=replace(item.observation, capture=CapturedOutput(b'changed', True)))
    elif case in {'after_stop', 'success_then_failure'}:
        item = attempt(intake, status='policy_rejected')
    history = (item, attempt(intake, 2)) if case == 'after_stop' else (item,)
    with pytest.raises(ValueError, match=reason):
        ExecutionCompletion.bind(intake, actor, RunOutcome(history, stop))


def test_policy_rejection_is_an_actual_observed_attempt():
    actor, intake, *_ = prepared()
    value = ExecutionCompletion.bind(intake, actor, RunOutcome((attempt(intake, status='policy_rejected'),), 'policy_rejected'))
    assert value.document().attempts[0].status == 'policy_rejected'
    with pytest.raises(ValueError, match='completion_status_mismatch'):
        ExecutionCompletion.bind(intake, actor, RunOutcome((), 'policy_rejected'))
    with pytest.raises(ValueError, match='completion_checkpoint_required'):
        ExecutionCompletion.bind(intake.planning, actor, RunOutcome((), 'provider_unconfigured'))


def test_actual_worker_observation_projects_original_hash(stored):
    worker, _, provider, intake = setup(stored)
    outcome = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    completion = ExecutionCompletion.bind(intake, stored.principal, outcome)
    assert completion.document().stop_reason == 'abstained' and len(provider.calls) == 1
    assert completion.document().attempts[0].attempt == outcome.latest.binding.reference()
