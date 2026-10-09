from threading import RLock
from types import SimpleNamespace

import pytest

from amphora_deployment.campaign_launch import managed_workers as module
from amphora_deployment.campaign_launch.managed_workers import ManagedLaunchWorkers
from amphora_deployment.campaign_launch.ports import PeerUnavailable
from amphora_deployment.campaign_launch.state import LaunchState
from amphora_deployment.profile import ProfileError


def binding(pin):
    return SimpleNamespace(profile=SimpleNamespace(fingerprint=pin, verify=lambda: None))


class Group:
    def __init__(self, bindings):
        self.slots = {name: SimpleNamespace(binding=value, thread=None) for name, value in bindings.items()}
        self.rows = {name: {'state': 'quiescent', 'faulted': False} for name in bindings}
        self.commands = []
        self.adoptions = 0
        self.detached = False

    def status(self): return self.rows
    def require_quiescent(self):
        if any(row['state'] != 'quiescent' or row['faulted'] for row in self.rows.values()):
            raise ProfileError('not_quiescent')
    def command(self, name, action):
        self.commands.append((name, action))
        if action == 'start': self.rows[name] = {'state': 'waiting', 'faulted': False}
        if action == 'recover': self.rows[name] = {'state': 'quiescent', 'faulted': False}
        if action == 'standby': self.rows[name] = {'state': 'standby', 'faulted': False}
        if action == 'quiesce': self.rows[name] = {'state': 'quiescent', 'faulted': False}
    def quiesce(self):
        for row in self.rows.values(): row['state'] = 'quiescent'
    def detach(self): self.detached = True
    def adopt(self): self.adoptions += 1


class Catalog:
    def __init__(self): self.stopped, self.started, self.draining = True, False, False
    def quiesce(self): self.draining = True
    def require_stopped(self):
        if not self.stopped: raise ProfileError('reporter_still_running')
    def start(self): self.started = True


@pytest.fixture
def managed_setup(monkeypatch, make_intent, admission_receipt, clock):
    monkeypatch.setattr(module, 'ScientificGroup', Group)
    monkeypatch.setattr(module, 'require_configured_pending', lambda *args: None)
    supervisor = SimpleNamespace(lock=RLock(), closed=False,
        processes={name: SimpleNamespace(status=lambda: {'state': 'running'}) for name in ('runtime', 'artifact', 'registry')},
        access=SimpleNamespace(require_running=lambda: None),
        scientific=Group({'science': binding('old')}), workers=Group({'advance': binding('native')}), catalog=Catalog())
    supervisor.scientific_command = lambda name, action: supervisor.scientific.command(name, action)
    supervisor.worker_command = lambda name, action: supervisor.workers.command(name, action)
    desired = {'science': binding('new')}
    store = SimpleNamespace(root='root', deployment_id='installation', prepare=lambda state: desired)
    adapter = ManagedLaunchWorkers(supervisor, store, lambda supervisor, bindings: Catalog())
    intent = make_intent()
    state = LaunchState.initial(intent, clock()).move('admission_unresolved', clock())
    return adapter, supervisor, state.observe_admission(admission_receipt(intent), clock())


def test_rebinding_waits_for_native_scientific_and_catalog_drain(managed_setup):
    adapter, supervisor, state = managed_setup
    original = supervisor.scientific
    supervisor.workers.command('advance', 'start')
    with pytest.raises(PeerUnavailable): adapter.prepare(state)
    assert supervisor.scientific is original
    supervisor.workers.quiesce()
    original.command('science', 'start')
    with pytest.raises(PeerUnavailable): adapter.prepare(state)
    original.quiesce(); supervisor.catalog.stopped = False
    with pytest.raises(PeerUnavailable): adapter.prepare(state)
    assert supervisor.catalog.draining and not original.detached
    supervisor.catalog.stopped = True
    assert adapter.prepare(state).quiescent
    assert original.detached and supervisor.scientific is not original
    assert supervisor.scientific.adoptions == 1 and supervisor.catalog.started


@pytest.mark.parametrize('dependency', ['runtime', 'artifact', 'registry', 'tls'])
def test_restored_launch_waits_for_dependencies_without_adoption_or_catalog_drain(managed_setup, dependency):
    adapter, supervisor, state = managed_setup
    if dependency == 'tls':
        def unavailable(): raise ProfileError('tool_tls_not_running')
        supervisor.access.require_running = unavailable
    else:
        supervisor.processes[dependency].status = lambda: {'state': 'not_started'}
    with pytest.raises(PeerUnavailable): adapter.prepare(state)
    assert supervisor.scientific.adoptions == 0
    assert not supervisor.catalog.draining and not supervisor.catalog.started
    assert not supervisor.scientific.commands and not supervisor.workers.commands


def test_engagement_and_restart_use_original_binding_without_duplicate_start(managed_setup):
    adapter, supervisor, state = managed_setup
    assert adapter.engage(state).ready == 2
    adapter.engage(state)
    assert supervisor.scientific.commands == [('science', 'start')]
    assert supervisor.workers.commands == [('advance', 'start')]
    restarted = ManagedLaunchWorkers(supervisor, adapter.store, adapter.catalog_factory)
    assert restarted.observe(state).ready == 2
    assert supervisor.scientific.adoptions == 2
    restarted.engage(state)
    assert supervisor.scientific.commands == [('science', 'start')]


def test_admission_standby_is_withdrawn_before_original_run_rebinding(managed_setup):
    adapter, supervisor, state = managed_setup
    original = supervisor.scientific
    original.command('science', 'standby')
    assert adapter.prepare(state).quiescent
    assert original.commands == [('science', 'standby'), ('science', 'quiesce')]
    assert original.detached and supervisor.scientific.commands == []


def test_outstanding_old_journal_blocks_replacement(managed_setup, monkeypatch):
    adapter, supervisor, state = managed_setup
    original = supervisor.scientific
    def block(*args): raise ProfileError('container_pending_binding_not_configured')
    monkeypatch.setattr(module, 'require_configured_pending', block)
    with pytest.raises(PeerUnavailable): adapter.prepare(state)
    assert supervisor.scientific is original and not original.detached


def test_partial_worker_failure_recovers_same_slot_then_drains(managed_setup):
    adapter, supervisor, state = managed_setup
    adapter.engage(state)
    original = supervisor.scientific
    original.rows['science'] = {'state': 'failed', 'faulted': True}
    assert adapter.observe(state).faulted
    assert not adapter.prepare(state).faulted
    assert supervisor.scientific is original
    assert original.commands[-1] == ('science', 'recover')
    assert adapter.engage(state).ready == 2
    assert adapter.drain(state).quiescent
    assert supervisor.catalog.draining


def test_drain_cannot_release_while_catalog_or_pending_journals_remain(managed_setup, monkeypatch):
    adapter, supervisor, state = managed_setup
    adapter.engage(state)
    supervisor.catalog.stopped = False
    assert not adapter.drain(state).quiescent
    supervisor.catalog.stopped = True
    def pending(*args): raise ProfileError('container_pending_binding_not_configured')
    monkeypatch.setattr(module, 'require_configured_pending', pending)
    assert not adapter.drain(state).quiescent
