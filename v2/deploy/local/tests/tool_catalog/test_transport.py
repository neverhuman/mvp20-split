import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.tool_catalog.transport import HeartbeatTransport


@pytest.mark.parametrize('mode', ['accepted', 'redirect', 'oversize', 'malformed', 'disconnect'])
def test_actual_loopback_transport_is_bounded_and_does_not_follow_redirects(mode):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append((self.path, self.headers['Authorization'],
                             json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            if mode == 'disconnect':
                self.close_connection = True
                return
            self.send_response(302 if mode == 'redirect' else 200)
            self.send_header('Location', 'http://127.0.0.1:1/never-follow')
            self.end_headers()
            self.wfile.write(b'x' * 8193 if mode == 'oversize' else b'{' if mode == 'malformed' else b'{"ok":true}')

        def log_message(self, *_):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        client = HeartbeatTransport(server.server_port, 'synthetic-private-token')
        if mode == 'accepted':
            assert client.send({'fixture': True}) == {'ok': True}
        else:
            with pytest.raises(ProfileError) as error:
                client.send({'fixture': True})
            assert 'synthetic-private-token' not in str(error.value)
        assert requests == [('/v1/registry/heartbeat', 'Bearer synthetic-private-token', {'fixture': True})]
        assert 'synthetic-private-token' not in repr(client)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize(('port', 'token'), [(True, 'valid-token-value'), (0, 'valid-token-value'),
    (65536, 'valid-token-value'), (1234, 'header\r\ninjection-value')])
def test_invalid_transport_settings_are_rejected(port, token):
    with pytest.raises(ProfileError):
        HeartbeatTransport(port, token)
