import pytest
from amphora_deployment.lifecycle.supervisor import Supervisor
from amphora_deployment.profile import ProfileError


class Turn:
    def __init__(self):
        self.code = None

    def poll(self):
        return self.code

    def release(self):
        assert self.code is not None

    def force_stop(self):
        self.code = 9


class Worker:
    def launch(self):
        self.turn = Turn()
        return self.turn

    def recover(self):
        pass


class Owner:
    def __init__(self):
        self.state = 'running'

    def status(self):
        return {'state': self.state}

    def force_stop(self):
        self.state = 'exited'

    def drain(self):
        self.state = 'exited'
        return self.status()


class Binding:
    def launch(self, events):
        return Owner()


def supervisor():
    worker = Worker()
    return Supervisor({'runtime': Binding()}, None, workers={'runtime-coordinate': worker}), worker


def test_apis_cannot_drain_restart_force_or_close_until_worker_quiescence():
    host, worker = supervisor()
    with pytest.raises(ProfileError, match='running_owners'):
        host.worker_command('runtime-coordinate', 'start')
    host.start('runtime')
    host.worker_command('runtime-coordinate', 'start')
    host.tick()
    for action in (lambda: host.drain('runtime'), lambda: host.restart('runtime'),
                   lambda: host.force_stop('runtime'), host.close):
        with pytest.raises(ProfileError, match='worker_requires_quiescence'):
            action()
    host.worker_command('runtime-coordinate', 'quiesce')
    assert worker.turn.code is None
    with pytest.raises(ProfileError, match='worker_requires_quiescence'):
        host.drain('runtime')
    worker.turn.code = 0
    host.tick()
    host.drain('runtime')
    host.close()
    with pytest.raises(ProfileError, match='lifecycle_closed'):
        host.worker_command('runtime-coordinate', 'start')


def test_owner_exit_quiesces_without_interrupt_or_automatic_resume():
    host, worker = supervisor()
    host.start('runtime')
    host.worker_command('runtime-coordinate', 'start')
    host.tick()
    host.processes['runtime'].state = 'exited'
    host.tick()
    assert worker.turn.code is None
    assert host.workers.status()['runtime-coordinate']['state'] == 'quiescing'
    worker.turn.code = 0
    host.tick()
    host.restart('runtime')
    host.tick()
    assert host.workers.status()['runtime-coordinate']['state'] == 'quiescent'


def test_forced_worker_stop_is_failure_not_graceful_quiescence():
    host, _ = supervisor()
    host.start('runtime')
    host.worker_command('runtime-coordinate', 'start')
    host.tick()
    assert host.worker_command('runtime-coordinate', 'force-stop')['state'] == 'failed'
    with pytest.raises(ProfileError, match='worker_requires_quiescence'):
        host.drain('runtime')
    host.worker_command('runtime-coordinate', 'recover')
    host.drain('runtime')


def test_worker_then_transport_then_api_shutdown_order():
    class Listener:
        def __init__(self):
            self.state = 'running'
        def status(self):
            return {'state': self.state}
        def drain(self):
            self.state = 'drained'
            return self.status()
        def require_stopped(self):
            if self.state != 'drained':
                raise ProfileError('tool_tls_requires_drain')
    class Access:
        def launch(self):
            return Listener()
    worker = Worker()
    host = Supervisor({'runtime': Binding()}, None, workers={'runtime-coordinate': worker},
                      access={'runtime': Access()})
    host.start('runtime')
    with pytest.raises(ProfileError, match='tool_tls_requires_running'):
        host.worker_command('runtime-coordinate', 'start')
    host.access_command('runtime', 'start')
    host.worker_command('runtime-coordinate', 'start')
    host.tick()
    with pytest.raises(ProfileError, match='worker_requires_quiescence'):
        host.access_command('runtime', 'drain')
    host.worker_command('runtime-coordinate', 'quiesce')
    worker.turn.code = 0
    host.tick()
    with pytest.raises(ProfileError, match='tool_tls_requires_drain'):
        host.drain('runtime')
    host.access_command('runtime', 'drain')
    host.drain('runtime')
    host.close()
