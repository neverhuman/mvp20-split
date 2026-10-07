import json
import threading
import time
import urllib.error
import urllib.request

from amphora_deployment.lifecycle.control import ControlServer
from amphora_deployment.lifecycle.supervisor import Supervisor

from .test_monitor import Binding, wait_for


def test_control_remains_responsive_while_scientific_observation_is_blocked():
    class Owner:
        state = 'running'
        def status(self):
            return {'state': self.state}
        def drain(self):
            self.state = 'exited'
            return self.status()
        def force_stop(self):
            self.state = 'exited'
    class OwnerBinding:
        def launch(self, events):
            return Owner()
    binding = Binding()
    supervisor = Supervisor({'runtime': OwnerBinding()}, None, scientific={'evolution-seed': binding})
    supervisor.start('runtime')
    token = 'synthetic-control-token-0000000000000000'
    server = ControlServer(0, supervisor, token)
    thread = threading.Thread(target=server.serve)
    thread.start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path, method='GET', credential=token):
        req = urllib.request.Request('http://127.0.0.1:' + str(server.server_port) + path, method=method,
                                     headers={'Authorization': 'Bearer ' + credential})
        try:
            response = opener.open(req, timeout=2)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read(65536))
    try:
        assert request('/scientific-workers/evolution-seed/start', 'POST', 'wrong')[0] == 401
        assert request('/scientific-workers/evolution-seed/start', 'POST')[0] == 200
        assert binding.entered.wait(2)
        started = time.monotonic()
        code, status = request('/status')
        assert code == 200 and status['scientific_workers']['evolution-seed']['active_turn']
        assert time.monotonic() - started < .5
        assert request('/scientific-workers/evolution-seed/quiesce', 'POST')[1]['state'] == 'quiescing'
        assert request('/owners/runtime/drain', 'POST')[0] == 409
        binding.finish.set()
        wait_for(lambda: supervisor.scientific.status()['evolution-seed']['state'] == 'quiescent')
        assert request('/owners/runtime/drain', 'POST')[0] == 200
        assert request('/shutdown', 'POST')[0] == 200
    finally:
        binding.finish.set()
        server.stopping = True
        thread.join(5)
        supervisor.scientific.detach()
        assert not thread.is_alive()
