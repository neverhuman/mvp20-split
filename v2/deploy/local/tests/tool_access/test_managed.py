import http.server
import json
import threading
import time
from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.tool_access.configuration import load_access
from amphora_deployment.tool_access.managed import AccessBinding, AccessGroup
from amphora_deployment.tool_access.proxy import OwnerRoute

from .test_proxy import TOKEN, connection


def test_managed_tls_drain_waits_for_accepted_response(identity):
    entered, release = threading.Event(), threading.Event()
    class SlowOwner(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            entered.set()
            assert release.wait(10)
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'{}')

        def log_message(self, *_):
            pass
    owner = http.server.ThreadingHTTPServer(('127.0.0.1', 0), SlowOwner)
    owner_thread = threading.Thread(target=owner.serve_forever)
    owner_thread.start()
    group = AccessGroup({'runtime': AccessBinding(identity, OwnerRoute('runtime', owner.server_port), 0)})
    response = []
    request_thread = None
    try:
        with pytest.raises(ProfileError, match='requires_running'):
            group.require_running()
        first = group.start('runtime')
        assert group.start('runtime') == first
        group.require_running()
        def request():
            client = connection(identity, first['port'])
            client.request('GET', '/v1/probe', headers={'Authorization': 'Bearer ' + TOKEN})
            result = client.getresponse()
            response.append((result.status, result.read()))
            client.close()
        request_thread = threading.Thread(target=request)
        request_thread.start()
        assert entered.wait(5)
        assert group.drain('runtime')['state'] == 'draining'
        assert group.drain('runtime')['state'] == 'draining'
        for operation in (group.require_stopped, lambda: group.restart('runtime')):
            with pytest.raises(ProfileError, match='requires_drain'):
                operation()
        release.set()
        request_thread.join(5)
        assert response == [(200, b'{}')]
        deadline = time.monotonic() + 5
        while group.status()['runtime']['state'] != 'drained':
            assert time.monotonic() < deadline
            time.sleep(.01)
        group.require_stopped()
        assert group.restart('runtime')['state'] == 'running'
    finally:
        release.set()
        if request_thread is not None:
            request_thread.join(5)
        group.close()
        owner.shutdown()
        owner.server_close()
        owner_thread.join(5)


def test_managed_config_binds_identity_and_fixed_upstream(identity, tmp_path):
    path = tmp_path / 'access.json'
    record = {'profile': 'local-tool-access-v1', 'identity_directory': str(identity.directory),
              'ports': {'runtime': 23458}}
    path.write_text(json.dumps(record))
    routes = SimpleNamespace(ports=(('runtime', 23457),), port=lambda _: 23457)
    binding = load_access(path, identity.deployment_id, routes, {'runtime': object()})['runtime']
    assert binding.route == OwnerRoute('runtime', 23457)
    assert binding.port == 23458
    with pytest.raises(ProfileError, match='deployment_mismatch'):
        load_access(path, 'wrong-deployment', routes, {'runtime': object()})
    record['ports']['runtime'] = 23457
    path.write_text(json.dumps(record))
    with pytest.raises(ProfileError, match='configuration_ports'):
        load_access(path, identity.deployment_id, routes, {'runtime': object()})


def test_changed_identity_never_starts_listener(identity):
    binding = AccessBinding(identity, OwnerRoute('runtime', 23457), 0)
    identity.certificate.write_bytes(identity.certificate.read_bytes() + b'changed')
    with pytest.raises(ProfileError, match='identity_digest'):
        binding.launch()


def test_group_cleanup_attempts_all_listeners_after_drain_or_close_failure():
    calls = []
    class Listener:
        def __init__(self, name, fail):
            self.name, self.fail = name, fail
        def drain(self):
            raise OSError('Cannot allocate another thread')
        def close(self):
            calls.append(self.name)
            if self.fail:
                raise OSError('Private socket failure')
    group = AccessGroup({})
    group.listeners = {'runtime': Listener('runtime', True), 'artifact': Listener('artifact', False)}
    with pytest.raises(ProfileError, match='tool_tls_cleanup_incomplete'):
        group.close()
    assert calls == ['runtime', 'artifact']
    group.listeners['runtime'].fail = False
    group.close()
