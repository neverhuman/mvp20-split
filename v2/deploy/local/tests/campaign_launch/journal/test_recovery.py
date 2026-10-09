from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_deployment.campaign_launch.intent import LaunchError
from amphora_deployment.campaign_launch.journal import LaunchJournal


def test_restart_replays_original_admission_intent_and_profile(make_intent, clock, tmp_path):
    intent = make_intent(); journal = LaunchJournal(tmp_path)
    first = journal.submit(intent, lambda i: None, now=clock)
    pending = journal.change(intent.key, first.revision, lambda s: s.move('admission_unresolved', clock()))
    reopened = LaunchJournal(tmp_path)
    assert reopened.active() == pending
    def should_not_reauthorize_historical_profile(_): raise AssertionError('Replay must retain original policy')
    assert reopened.submit(intent, should_not_reauthorize_historical_profile, now=clock) == pending
    assert reopened.active().intent.admission.canonical_bytes == intent.admission.canonical_bytes
    with pytest.raises(LaunchError, match='launch_request_conflict'):
        reopened.submit(make_intent(profile='e' * 64), lambda i: None, now=clock)


def test_two_concurrent_launches_cannot_reserve_two_active_slots(make_intent, clock, tmp_path):
    journal = LaunchJournal(tmp_path); barrier = Barrier(2)
    def submit(name):
        barrier.wait()
        try: return journal.submit(make_intent(name), lambda i: None, now=clock).phase
        except LaunchError as error: return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, ['first', 'second'])) == ['launch_slot_busy', 'preparing']


def test_stale_transition_and_exception_rollback_leave_request_unchanged(make_intent, clock, tmp_path):
    journal = LaunchJournal(tmp_path); first = journal.submit(make_intent(), lambda i: None, now=clock)
    def failure(_): raise RuntimeError('injected')
    with pytest.raises(RuntimeError): journal.change(first.intent.key, 0, failure)
    assert journal.active() == first
    pending = journal.change(first.intent.key, 0, lambda s: s.move('admission_unresolved', clock()))
    with pytest.raises(LaunchError, match='launch_revision_conflict'):
        journal.change(first.intent.key, 0, lambda s: s.move('rejected', clock()))
    assert journal.active() == pending


def test_admitted_run_survives_worker_failure_and_blocks_other_launches(make_intent, admission_receipt, clock, tmp_path):
    journal = LaunchJournal(tmp_path); intent = make_intent()
    journal.submit(intent, lambda i: None, now=clock)
    journal.change(intent.key, 0, lambda s: s.move('admission_unresolved', clock()))
    accepted = journal.change(intent.key, 1, lambda s: s.observe_admission(admission_receipt(intent), clock()))
    failed = journal.change(intent.key, accepted.revision, lambda s: s.move('recovery_required', clock(), 'worker_binding_unavailable'))
    assert LaunchJournal(tmp_path).active().run_id == 'run-1'
    assert failed.admission == accepted.admission
    with pytest.raises(LaunchError, match='launch_slot_busy'):
        journal.submit(make_intent('second'), lambda i: None, now=clock)


def test_rejected_request_frees_slot_without_erasing_its_receipt(make_intent, clock, tmp_path):
    journal = LaunchJournal(tmp_path); first = journal.submit(make_intent(), lambda i: None, now=clock)
    rejected = journal.change(first.intent.key, 0, lambda s: s.move('rejected', clock(), 'input_unavailable'))
    assert journal.active() is None
    journal.submit(make_intent('second'), lambda i: None, now=clock)
    assert journal.get(first.intent.key) == rejected
