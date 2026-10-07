import json
import threading
import urllib.error
import urllib.request

from amphora_deployment.lifecycle.control import ControlServer
from amphora_deployment.lifecycle.supervisor import Supervisor


class Binding:
    def launch(self, events):
        raise AssertionError('Unauthenticated request must not launch a process')


def test_actual_loopback_control_requires_auth_and_rejects_command_payloads():
    server = ControlServer(0, Supervisor({'registry': Binding()}, None), 'engineering-control-token-1234567890')
    thread = threading.Thread(target=server.serve)
    thread.start()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    endpoint = 'http://127.0.0.1:' + str(server.server_port)
    def request(path, *, method='GET', token=None, body=None):
        headers = {} if token is None else {'Authorization':'Bearer '+token}
        req = urllib.request.Request(endpoint+path, method=method, headers=headers, data=body)
        try:
            response = opener.open(req, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())
    try:
        assert request('/status')[0] == 401
        assert request('/owners/registry/start', method='POST')[0] == 401
        token = 'engineering-control-token-1234567890'
        status, result = request('/status', token=token)
        assert status == 200 and result['owners']['registry']['state'] == 'not_started'
        assert request('/owners/registry/start', method='POST', token=token, body=b'{"command":"arbitrary"}')[0] == 400
        assert request('/owners/unknown/start', method='POST', token=token)[0] == 409
        assert request('/shutdown', method='POST', token=token)[0] == 200
    finally:
        server.stopping = True
        thread.join(timeout=5)
        assert not thread.is_alive()
