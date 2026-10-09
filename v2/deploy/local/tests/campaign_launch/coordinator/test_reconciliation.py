import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from amphora_contracts_graph_runtime import GraphRunPage
from amphora_deployment.campaign_launch.coordinator import LaunchCoordinator
from amphora_deployment.campaign_launch.journal import LaunchJournal
from amphora_deployment.campaign_launch.ports import PeerUnavailable, PreflightRejected, WorkerObservation


class Peers:
    def __init__(self, journal, receipt):
        self.journal, self.accepted = journal, receipt
        self.stored = None
        self.submissions = []
        self.lost_reply = False
        self.offline = False
        self.reject = False
        self.status = 'running'
        self.wrong_run = False
        self.worker_failure = False
        self.drained = False
        self.starts = 0

    def check(self, intent):
        if self.offline: raise PeerUnavailable()
        if self.reject: raise PreflightRejected()

    def receipt(self, intent):
        if self.offline: raise PeerUnavailable()
        return self.stored

    def admit(self, intent):
        assert self.journal.active().phase == 'admission_unresolved'
        self.submissions.append(intent.admission.canonical_bytes)
        self.stored = self.accepted
        if self.lost_reply: raise PeerUnavailable()
        return self.accepted

    def run(self, state):
        if self.offline: raise PeerUnavailable()
        return GraphRunPage.model_validate_json(json.dumps({
            'scope': state.intent.admission.identity.scope.model_dump(),
            'run_id': 'wrong-run' if self.wrong_run else state.run_id,
            'plan_sha256': 'a' * 64, 'status': self.status, 'revision': 1,
            'node_count': 0, 'budget_limit': 8, 'reserved': 0, 'spent': 0,
            'stop_reason': None, 'nodes': [], 'next_after': None}))

    def prepare(self, state):
        return WorkerObservation(2, 0, not self.worker_failure, self.worker_failure)

    def engage(self, state):
        assert self.journal.active().phase == 'engaging'
        self.starts += 1
        return WorkerObservation(2, 1 if self.worker_failure else 2, False, self.worker_failure)

    def observe(self, state):
        return WorkerObservation(2, 1 if self.worker_failure else 2, False, self.worker_failure)

    def drain(self, state):
        assert self.journal.active().phase == 'draining'
        return WorkerObservation(2, 0, self.drained)


@pytest.fixture
def setup(tmp_path, make_intent, admission_receipt, clock):
    journal = LaunchJournal(tmp_path)
    intent = make_intent()
    journal.submit(intent, lambda i: None, now=clock)
    peers = Peers(journal, admission_receipt(intent))
    coordinator = LaunchCoordinator(journal, peers, peers, peers, now=clock)
    return journal, peers, coordinator


def test_lost_admission_reply_then_restart_recovers_original_receipt(setup, clock, tmp_path):
    journal, peers, coordinator = setup
    peers.lost_reply = True
    assert coordinator.tick().phase == 'admission_unresolved'
    assert coordinator.tick().reason == 'launch_peer_unavailable'
    assert len(peers.submissions) == 1
    reopened = LaunchJournal(tmp_path)
    restarted = LaunchCoordinator(reopened, peers, peers, peers, now=clock)
    state = restarted.tick()
    assert state.phase == 'admitted_not_engaged' and state.run_id == 'run-1'
    assert len(peers.submissions) == 1
    assert peers.submissions[0] == state.intent.admission.canonical_bytes


def test_missing_receipt_replays_identical_bytes_never_another_command(setup):
    journal, peers, coordinator = setup
    peers.lost_reply = True
    coordinator.tick(); coordinator.tick()
    peers.stored = None  # Read lag/verified absence still cannot mint a new request.
    peers.lost_reply = False
    assert coordinator.tick().run_id == 'run-1'
    assert len(peers.submissions) == 2 and peers.submissions[0] == peers.submissions[1]


def test_peer_outage_does_not_reject_or_release_reserved_slot(setup):
    journal, peers, coordinator = setup
    peers.offline = True
    assert coordinator.tick().phase == 'preparing'
    peers.offline = False
    coordinator.tick()
    peers.offline = True
    assert coordinator.tick().phase == 'admission_unresolved'
    assert journal.active() is not None and peers.submissions == []


def test_definitive_preflight_rejection_never_contacts_admission(setup):
    journal, peers, coordinator = setup
    peers.reject = True
    assert coordinator.tick().phase == 'rejected'
    assert journal.active() is None and peers.submissions == []


def test_terminal_run_does_not_release_until_workers_are_drained(setup):
    journal, peers, coordinator = setup
    assert [coordinator.tick().phase for _ in range(4)] == [
        'admission_unresolved', 'admitted_not_engaged', 'engaging', 'engaged']
    peers.status = 'completed'
    assert coordinator.tick().phase == 'draining'
    assert coordinator.tick().phase == 'draining'
    assert journal.active() is not None
    peers.drained = True
    result = coordinator.tick()
    assert result.phase == 'released' and result.run_id == 'run-1'
    assert journal.active() is None


def test_worker_failure_preserves_admitted_run_and_original_bindings(setup):
    journal, peers, coordinator = setup
    for _ in range(3): coordinator.tick()
    peers.worker_failure = True
    state = coordinator.tick()
    assert state.phase == 'admitted_not_engaged' and state.run_id == 'run-1'
    assert state.ready_workers == 1 and state.admission == peers.accepted
    assert coordinator.tick().phase == 'admitted_not_engaged'
    assert peers.starts == 1 and len(peers.submissions) == 1


def test_wrong_run_response_latches_without_starting_workers(setup):
    journal, peers, coordinator = setup
    coordinator.tick(); coordinator.tick()
    peers.wrong_run = True
    assert coordinator.tick().phase == 'recovery_required'
    assert coordinator.tick().run_id == 'run-1'
    assert peers.starts == 0


def test_later_worker_failure_keeps_partial_readiness_and_reconciles_same_run(setup):
    journal, peers, coordinator = setup
    for _ in range(4): coordinator.tick()
    unchanged = journal.active()
    assert coordinator.tick() == unchanged
    peers.worker_failure = True
    state = coordinator.tick()
    assert state.phase == 'admitted_not_engaged' and state.ready_workers == 1
    peers.worker_failure = False
    coordinator.tick()
    assert coordinator.tick().phase == 'engaged'
    assert len(peers.submissions) == 1 and journal.active().run_id == 'run-1'


def test_complete_before_engagement_drains_without_starting(setup):
    journal, peers, coordinator = setup
    coordinator.tick(); coordinator.tick()
    peers.status = 'failed'
    assert coordinator.tick().phase == 'draining'
    peers.drained = True
    assert coordinator.tick().phase == 'released'
    assert peers.starts == 0


def test_overlapping_ticks_do_not_submit_twice(setup):
    journal, peers, coordinator = setup
    coordinator.tick()
    entered, release = Event(), Event()
    original = peers.admit
    def slow_admit(intent):
        entered.set()
        assert release.wait(5)
        return original(intent)
    peers.admit = slow_admit
    with ThreadPoolExecutor(max_workers=1) as pool:
        task = pool.submit(coordinator.tick)
        try:
            assert entered.wait(5)
            assert coordinator.tick() is None
        finally:
            release.set()
        assert task.result().run_id == 'run-1'
    assert len(peers.submissions) == 1
