import pytest

from amphora_deployment.lifecycle.supervisor import Supervisor
from amphora_deployment.profile import ProfileError


class Process:
    def __init__(self):
        self.state = 'running'

    def status(self):
        return {'state':self.state}

    def force_stop(self):
        self.state = 'exited'


class Binding:
    def __init__(self):
        self.calls = 0

    def launch(self, events):
        self.calls += 1
        return Process()


def test_repeat_start_does_not_create_duplicate_or_retry_failed_owner():
    binding = Binding()
    supervisor = Supervisor({'runtime': binding}, None)
    assert supervisor.status()['runtime']['state'] == 'not_started'
    assert supervisor.start('runtime') == supervisor.start('runtime')
    assert binding.calls == 1
    supervisor.processes['runtime'].state = 'exited'
    assert supervisor.start('runtime')['state'] == 'exited'
    assert binding.calls == 1
    supervisor.restart('runtime')
    assert binding.calls == 2


def test_shutdown_and_restart_do_not_force_running_owner():
    supervisor = Supervisor({'runtime': Binding()}, None)
    supervisor.start('runtime')
    with pytest.raises(ProfileError, match='requires_stop'):
        supervisor.close()
    with pytest.raises(ProfileError, match='requires_stop'):
        supervisor.restart('runtime')
    assert supervisor.force_stop('runtime') == supervisor.force_stop('runtime')
    supervisor.close()
    with pytest.raises(ProfileError):
        supervisor.start('runtime')
    with pytest.raises(ProfileError):
        supervisor.start('unknown')
