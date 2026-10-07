"""Fixed-cardinality transport counters; never retain request or exception text."""

import threading

STAGES = ('handshake', 'request_body', 'connect', 'request', 'response_headers',
          'response_body', 'client_response', 'handler', 'deadline')
KINDS = ('timeout', 'io', 'http', 'truncated', 'oversized')


class TransportDiagnostics:
    def __init__(self):
        self._lock = threading.Lock()
        self._failures = {}
        self._responses = {}

    def failure(self, stage, kind):
        if stage not in STAGES or kind not in KINDS:
            raise ValueError('tool_tls_diagnostic_category')
        key = stage + '.' + kind
        with self._lock:
            self._failures[key] = self._failures.get(key, 0) + 1

    def response(self, status):
        if type(status) is not int or not 100 <= status <= 599:
            raise ValueError('tool_tls_diagnostic_status')
        key = str(status // 100) + 'xx'
        with self._lock:
            self._responses[key] = self._responses.get(key, 0) + 1

    def snapshot(self):
        with self._lock:
            return {'failures': dict(self._failures), 'responses': dict(self._responses)}
