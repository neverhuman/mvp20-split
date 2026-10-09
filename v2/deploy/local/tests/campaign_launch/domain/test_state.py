import pytest
import json
from amphora_deployment.campaign_launch.intent import LaunchError
from amphora_deployment.campaign_launch.state import LaunchState


def test_admission_requires_durable_intent_and_cannot_change_terminal_receipt(make_intent, admission_receipt, clock):
    intent = make_intent(); state = LaunchState.initial(intent, clock())
    with pytest.raises(LaunchError, match='launch_admission_intent_required'):
        state.observe_admission(admission_receipt(intent), clock())
    state = state.move('admission_unresolved', clock()).observe_admission(admission_receipt(intent, 'pending'), clock())
    with pytest.raises(LaunchError, match='launch_admission_binding'):
        state.observe_admission(admission_receipt(intent, operation='changed'), clock())
    state = state.observe_admission(admission_receipt(intent), clock())
    assert state.observe_admission(admission_receipt(intent), clock()) is state
    with pytest.raises(LaunchError, match='launch_admission_changed'):
        state.observe_admission(admission_receipt(intent, run='different'), clock())
    with pytest.raises(LaunchError): state.move('rejected', clock())


def test_engagement_requires_all_expected_workers_and_preserves_run_on_failure(make_intent, admission_receipt, clock):
    intent = make_intent()
    state = LaunchState.initial(intent, clock()).move('admission_unresolved', clock())
    state = state.observe_admission(admission_receipt(intent), clock()).move('engaging', clock())
    with pytest.raises(LaunchError, match='launch_workers_not_ready'): state.move('engaged', clock())
    state = state.readiness(2, 1, clock())
    with pytest.raises(LaunchError, match='launch_workers_not_ready'): state.move('engaged', clock())
    state = state.readiness(2, 2, clock()).move('engaged', clock())
    assert state.run_id == 'run-1'
    assert LaunchState.restore(intent, state.receipt().model_dump_json().encode()) == state


@pytest.mark.parametrize('mutation', ['wrong_kind', 'wrong_revision', 'pending_engaged', 'empty_engaged'])
def test_restore_rejects_inconsistent_durable_admission(make_intent, admission_receipt, clock, mutation):
    intent = make_intent()
    state = LaunchState.initial(intent, clock()).move('admission_unresolved', clock())
    state = state.observe_admission(admission_receipt(intent), clock())
    record = state.receipt().model_dump(mode='json')
    if mutation == 'wrong_kind': record['admission']['outcome']['committed']['kind'] = 'attempt'
    if mutation == 'wrong_revision': record['admission']['outcome']['committed']['revision'] = 1
    if mutation == 'pending_engaged':
        record['admission'] = admission_receipt(intent, 'pending').model_dump(mode='json')
        record['run_id'] = None
        record['phase'] = 'engaged'
    if mutation == 'empty_engaged': record['phase'] = 'engaged'
    with pytest.raises(LaunchError, match='launch_journal_corrupt'):
        LaunchState.restore(intent, json.dumps(record).encode())
