"""Pinned TLS handshakes and read-only owner probes; no widening of tool routes."""

import http.client
import json
import socket
import ssl

from ..profile import require
from ..tool_access.identity import HOSTNAME


class ToolDependencies:
    def __init__(self, certificate, runtime_port, artifact_port, runtime_upstream, artifact_upstream):
        require(all(type(port) is int and 1024 <= port <= 65535 for port in
                    (runtime_port, artifact_port, runtime_upstream, artifact_upstream))
                and runtime_port != artifact_port, 'catalog_dependency_ports')
        self.certificate, self.runtime_port, self.artifact_port = certificate, runtime_port, artifact_port
        self.runtime_upstream, self.artifact_upstream = runtime_upstream, artifact_upstream

    def _trusted(self, port):
        context = ssl.create_default_context(cafile=str(self.certificate))
        with socket.create_connection(('127.0.0.1', port), timeout=1) as raw, context.wrap_socket(raw, server_hostname=HOSTNAME):
            pass

    def _read(self, port, path):
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=1)
        try:
            connection.request('GET', path, headers={'Connection': 'close'})
            response = connection.getresponse()
            require(response.status == 200, 'catalog_dependency_http')
            body = response.read(8193)
            require(len(body) <= 8192, 'catalog_dependency_size')
            return json.loads(body)
        finally:
            connection.close()

    def __call__(self):
        self._trusted(self.runtime_port)
        self._trusted(self.artifact_port)
        runtime = self._read(self.runtime_upstream, '/health')
        artifact = self._read(self.artifact_upstream, '/ready')
        # Runtime health reports configured execution, not continuous SQL readiness.
        return (type(runtime) is dict and runtime.get('status') == 'ok' and runtime.get('execution_available') is True
                and type(artifact) is dict and artifact.get('ready') is True)
