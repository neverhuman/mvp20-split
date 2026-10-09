from threading import Event
from types import SimpleNamespace

from amphora_deployment.campaign_launch import host as module
from amphora_deployment.campaign_launch.host import LaunchHost
from amphora_deployment.lifecycle.supervisor import Supervisor
from amphora_deployment.profile import ProfileError
import pytest


def make_host(monkeypatch, tick):
    monkeypatch.setattr(module, 'LaunchCoordinator', lambda *args: SimpleNamespace(tick=tick, request_recovery=lambda key: None))
    installation = SimpleNamespace(store=object(), policy=object(), executors=[], journal=object(), catalog=lambda *args: None,
        manifest=SimpleNamespace(actor_id='researcher'))
    supervisor = SimpleNamespace(closed=False, bindings={name: SimpleNamespace(environment={
        'AMPHORA_' + name.upper() + '_OPERATOR_TOKEN': 'fixture-private-token'})
        for name in ('runtime', 'artifact', 'registry')})
    return LaunchHost(installation, supervisor, SimpleNamespace(port=lambda name: 57018))


def test_api_remains_readable_after_coordinator_failure_then_closes(monkeypatch):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    def fail(): raise OSError('private-detail')
    host = make_host(monkeypatch, fail)
    host.attach_api(0, 'x' * 40)
    port = host.api.server_address[1]
    host.start()
    assert host.stop.wait(3)
    assert not host.api_stop.is_set() and not host.api.accepting()
    try:
        # Route remains served, even though coordinator acceptance has stopped.
        with pytest.raises(HTTPError) as error:
            urlopen(Request(f'http://127.0.0.1:{port}/v1/unknown', headers={'Authorization': 'Bearer ' + 'x' * 40}), timeout=3)
        assert error.value.code == 404
        error.value.close()
    finally:
        host.close()
    assert not host.api_thread.is_alive()


def test_unstarted_listener_is_closed_with_host(monkeypatch):
    host = make_host(monkeypatch, lambda: None)
    host.attach_api(0, 'x' * 40)
    host.close()
    assert host.api.socket.fileno() == -1


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
