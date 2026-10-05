"""Independent event oracles preserve uncertainty and exact typed owner outcomes."""

import json
from dataclasses import replace
from datetime import timedelta

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.campaign_dispatch import (
    CompilerEffect,
    CompilerEvent,
    CompilerObservation,
    CompilerSelection,
)
from amphora_agent_planning.campaign_eligibility import (
    EligibilityBatch,
    EligibilityConfiguration,
)
from amphora_contracts_tools import RegistryReceipt

from ..campaign_authoring.test_values import plan, receipt, saved, validation
from ..campaign_eligibility.test_observations import NOW, response


@pytest.fixture(scope='module')
def operations():
    authoring = plan(tools=True)
    document = authoring.review.composition.evidence.proposal.attempt.request.document()
    principal = Principal(document.actor_id, document.reference.scope, frozenset({'read_attempts', 'record_attempts'}))
    config = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='e' * 64)
    selection = CompilerSelection.bind(principal, authoring, config)
    args = selection, principal, authoring, config
    request = EligibilityBatch.bind(authoring.review, authoring.budget, config, 'original').requests[0]
    return selection, {
        'save': (CompilerEffect.authoring(*args), authoring.save()),
        'validate': (CompilerEffect.authoring(*args, saved=saved(authoring)), authoring.validate(saved(authoring))),
        'resolve': (CompilerEffect.eligibility(*args, 'original', request.selected.document().lock.descriptor_sha256), request),
    }, saved(authoring)


def advance(selection, effect, request, previous, action, data=None):
    position = 1 if previous is None else previous.position + 1
    event = CompilerEvent.record(effect, position, action, data)
    assert len(event.sha256) == 64
    return event.apply(previous, selection, effect, request, position)


@pytest.mark.parametrize('kind,status', [('save', 'saved'), ('validate', 'compiled'), ('validate', 'structural_invalid'),
                                      ('save', 'pending'), ('save', 'rejected'), ('save', 'awaiting_readback'),
                                      ('resolve', 'candidate'), ('resolve', 'rejected')])
def test_typed_outcomes_preserve_each_owner_state(operations, kind, status):
    selection, choices, stored = operations
    effect, request = choices[kind]
    if kind == 'resolve':
        record = response(request) if status == 'candidate' else RegistryReceipt.model_validate_json(json.dumps({
            'operation_id': 'negative', 'status': 'rejected', 'reason_code': 'release_not_active',
            'release': None, 'deployment': None, 'heartbeat': None, 'decision': None}))
        observation = CompilerObservation.bind(selection, effect, request, record)
    else:
        record = receipt(request, status=status if status in {'pending', 'rejected'} else 'accepted')
        readback = stored.readback if status == 'saved' else validation(request, valid=status == 'compiled') if kind == 'validate' else None
        observation = CompilerObservation.bind(selection, effect, request, record, readback)
    assert observation.status == status
    assert CompilerObservation.restore(observation.canonical, selection, effect, request) == observation
    progress = advance(selection, effect, request, None, 'prepared')
    progress = advance(selection, effect, request, progress, 'observed', json.loads(observation.canonical))
    assert progress.state == status and progress.dispatches == 0
    assert progress.terminal == (status not in {'pending', 'awaiting_readback'})
    if progress.terminal:
        with pytest.raises(ValueError, match='compiler_event_order_or_terminal'):
            advance(selection, effect, request, progress, 'dispatch')


def test_uncertain_and_blocked_never_mean_rejection(operations):
    selection, choices, _ = operations
    effect, request = choices['save']
    progress = advance(selection, effect, request, None, 'prepared')
    with pytest.raises(ValueError, match='compiler_event_uncertain'):
        advance(selection, effect, request, progress, 'uncertain')
    progress = advance(selection, effect, request, progress, 'dispatch')
    progress = advance(selection, effect, request, progress, 'uncertain')
    assert progress.state == 'uncertain' and progress.dispatches == 1 and not progress.terminal
    progress = advance(selection, effect, request, progress, 'blocked', 'owner_protocol')
    assert progress.reason == 'owner_protocol' and progress.observation is None and not progress.terminal
    progress = advance(selection, effect, request, progress, 'dispatch')
    assert progress.dispatches == 2 and progress.reason is None


def test_last_event_slot_reserved_for_exact_terminal_evidence(operations):
    selection, choices, stored = operations
    effect, request = choices['save']
    progress = advance(selection, effect, request, None, 'prepared')
    for _ in range(62):
        progress = advance(selection, effect, request, progress, 'blocked', 'owner_unavailable')
    with pytest.raises(ValueError, match='compiler_event_terminal_slot_reserved'):
        advance(selection, effect, request, progress, 'dispatch')
    result = CompilerObservation.bind(selection, effect, request, stored.receipt, stored.readback)
    terminal = advance(selection, effect, request, progress, 'observed', json.loads(result.canonical))
    assert terminal.position == 64 and terminal.state == 'saved'
    with pytest.raises(ValueError, match='compiler_event_limit'):
        CompilerEvent.record(effect, 65, 'observed')


def test_historical_candidate_is_not_a_freshness_grant(operations):
    selection, choices, _ = operations
    effect, request = choices['resolve']
    result = CompilerObservation.bind(selection, effect, request, response(request))
    assert result.status == 'candidate'
    with pytest.raises(ValueError, match='eligibility_expired'):
        result.outcome.require_fresh(NOW + timedelta(minutes=1))
    assert CompilerObservation.restore(result.canonical, selection, effect, request) == result


def test_same_registry_command_under_foreign_policy_is_not_original_observation(operations):
    selection, choices, _ = operations
    effect, request = choices['resolve']
    other = EligibilityConfiguration.bind(owner_id='registry-fixture', actor_id='planning-agent', policy_sha256='a' * 64)
    changed = request.bind(other, request.check_id, request.attempt, request.selected, request.context)
    assert changed.command == request.command
    with pytest.raises(ValueError, match='compiler_observation_configuration'):
        CompilerObservation.bind(selection, effect, changed, response(changed))


@pytest.mark.parametrize('fault', ['identity', 'position', 'action', 'data', 'boolean', 'whitespace', 'huge'])
def test_corrupt_event_cannot_assert_success(operations, fault):
    selection, choices, _ = operations
    effect, request = choices['save']
    first = advance(selection, effect, request, None, 'prepared')
    value = json.loads(CompilerEvent.record(effect, 2, 'dispatch').canonical)
    if fault == 'identity':
        value['effect_sha256'] = 'f' * 64
    elif fault == 'position':
        value['position'] = 3
    elif fault == 'action':
        value['action'] = 'saved'
    elif fault == 'data':
        value['action'], value['data'] = 'blocked', 'model_said_done'
    elif fault == 'boolean':
        value['position'] = True
    raw = canonical(value) + (b' ' if fault == 'whitespace' else b'')
    if fault == 'huge':
        raw = b'x' * 2101249
    with pytest.raises(ValueError):
        CompilerEvent(raw).apply(first, selection, effect, request, 2)


def test_foreign_observation_or_request_rejected(operations):
    selection, choices, stored = operations
    effect, request = choices['save']
    result = CompilerObservation.bind(selection, effect, request, stored.receipt, stored.readback)
    value = json.loads(result.canonical)
    value['effect_id'] = 'foreign'
    with pytest.raises(ValueError, match='compiler_observation_binding'):
        CompilerObservation.restore(canonical(value), selection, effect, request)
    with pytest.raises(ValueError, match='compiler_observation_owner'):
        CompilerObservation.bind(selection, effect, replace(request, owner_id='foreign'), stored.receipt, stored.readback)
