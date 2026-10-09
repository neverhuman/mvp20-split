from threading import Event
from types import SimpleNamespace

from amphora_deployment.campaign_launch import host as module
from amphora_deployment.campaign_launch.host import LaunchHost
from amphora_deployment.lifecycle.supervisor import Supervisor
from amphora_deployment.profile import ProfileError
import pytest


def make_host(monkeypatch, tick):
    monkeypatch.setattr(module, 'LaunchCoordinator', lambda *args: SimpleNamespace(tick=tick))
    installation = SimpleNamespace(store=object(), policy=object(), executors=[], journal=object(), catalog=lambda *args: None)
    supervisor = SimpleNamespace(bindings={name: SimpleNamespace(environment={
        'AMPHORA_' + name.upper() + '_OPERATOR_TOKEN': 'fixture-private-token'})
        for name in ('runtime', 'artifact', 'registry')})
    return LaunchHost(installation, supervisor, SimpleNamespace(port=lambda name: 57018))


def test_background_coordinator_stops_before_owner_lease_is_released(monkeypatch):
    entered = Event()
    host = make_host(monkeypatch, entered.set)
    host.start()
    assert entered.wait(3)
    host.close()
    host.require_stopped()
    assert not host.failure


def test_private_failure_latches_host_without_printing_exception(monkeypatch, capsys):
    def fail(): raise OSError('fixture-private-token')
    host = make_host(monkeypatch, fail)
    host.start()
    assert host.stop.wait(3)
    host.close()
    assert host.failure and capsys.readouterr().out == ''


def test_shutdown_does_not_close_while_launch_reconciliation_is_running():
    supervisor = Supervisor({'runtime': object()}, None)
    calls = []
    def busy(): raise ProfileError('launch_host_requires_drain')
    supervisor.launch = SimpleNamespace(quiesce=lambda: calls.append('quiesce'), require_stopped=busy)
    with pytest.raises(ProfileError, match='launch_host_requires_drain'): supervisor.close()
    assert calls == ['quiesce'] and not supervisor.closed
    supervisor.launch.require_stopped = lambda: None
    supervisor.close()
    assert supervisor.closed
