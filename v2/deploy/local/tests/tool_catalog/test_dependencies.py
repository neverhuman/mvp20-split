import json
import os
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from amphora_deployment.tool_access import TLSIdentity
from amphora_deployment.tool_access.managed import AccessBinding
from amphora_deployment.tool_access.proxy import OwnerRoute
from amphora_deployment.tool_catalog.dependencies import ToolDependencies

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Selected Windows TLS profile')


def test_actual_pinned_tls_observes_configured_execution_and_data_readiness(tmp_path):
    identity = TLSIdentity.create(tmp_path / 'tls', 'catalog-dependencies', Path('C:/Program Files/Git/usr/bin/openssl.exe'))
    values = {'/health': {'status': 'ok', 'execution_available': True}, '/ready': {'ready': True}}
    paths = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            body = json.dumps(values[self.path]).encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    upstream = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=upstream.serve_forever)
    thread.start()
    listeners = []
    try:
        for owner in ('runtime', 'artifact'):
            listeners.append(AccessBinding(identity, OwnerRoute(owner, upstream.server_port), 0).launch())
        probe = ToolDependencies(identity.certificate, *(listener.server.server_port for listener in listeners),
                                 upstream.server_port, upstream.server_port)
        assert probe() and paths == ['/health', '/ready']
        values['/health']['execution_available'] = False
        assert not probe()
        values['/health']['execution_available'] = True
        values['/ready']['ready'] = False
        assert not probe()
        foreign = TLSIdentity.create(tmp_path / 'foreign', 'foreign-catalog', Path('C:/Program Files/Git/usr/bin/openssl.exe'))
        probe.certificate = foreign.certificate
        with pytest.raises(ssl.SSLCertVerificationError):
            probe()
    finally:
        for listener in listeners:
            listener.close()
        upstream.shutdown()
        upstream.server_close()
        thread.join(5)
        assert not thread.is_alive()
