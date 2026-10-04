"""Closed authenticated reads with one wall-clock and aggregate byte budget."""

import http.client
import json
import math
import socket
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AcceptedGraphChange,
    DomainGraphRef,
    DomainGraphSnapshot,
    DomainRevisionRef,
    GraphAuthoringProfile,
)

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..proposals.context import canonical

ROUTES = {
    '/v1/graph-profiles/read': (DomainGraphRef, GraphAuthoringProfile, 262144),
    '/v1/graph-snapshots/read': (DomainRevisionRef, DomainGraphSnapshot, 16777216),
    '/v1/graph-changes/read': (AcceptedChangeRef, AcceptedGraphChange, 1048576),
}


class KnowledgeUnavailable(ValueError):
    """Unknown peer state, never a substitute graph or implicit retry."""


@dataclass
class KnowledgeReadWindow:
    seconds: float = 15
    deadline: float = field(init=False)
    calls: int = field(default=0, init=False)
    consumed: int = field(default=0, init=False)

    def __post_init__(self):
        require(type(self.seconds) in (int, float) and math.isfinite(self.seconds) and 0 < self.seconds <= 15,
                'knowledge_read_deadline')
        self.deadline = time.monotonic() + self.seconds

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise KnowledgeUnavailable('knowledge_read_expired')
        return remaining

    def start(self):
        self.remaining()
        require(self.calls < 3, 'knowledge_read_call_limit')
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        require(self.consumed <= 18087936, 'knowledge_read_byte_limit')


class KnowledgeTransport:
    def __init__(self, endpoint, token):
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, 'knowledge_peer_endpoint')
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and
                     parsed.port is not None and 1 <= parsed.port <= 65535 and
                     parsed.username is None and parsed.password is None and parsed.path in ('', '/') and
                     not parsed.query and not parsed.fragment and not any(c.isspace() for c in endpoint))
        except ValueError:
            valid = False
        require(valid, 'knowledge_peer_endpoint')
        require(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(c) <= 126 for c in token),
                'knowledge_peer_credential')
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def read(self, path, reference, window):
        require(type(path) is str and path in ROUTES, 'knowledge_peer_path')
        request_model, response_model, limit = ROUTES[path]
        reference = request_model.model_validate_json(reference.model_dump_json(warnings=False))
        body = canonical(reference)
        require(len(body) <= 4096, 'knowledge_request_size')
        window.start()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=window.remaining())
        timer = None
        try:
            connection.connect()
            active_socket = connection.sock

            def expire():
                try:
                    active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(window.remaining(), expire)
            timer.daemon = True
            timer.start()
            connection.request('POST', path, body, {'Authorization': 'Bearer ' + self._token,
                                                   'Content-Type': 'application/json'})
            active_socket.settimeout(window.remaining())
            response = connection.getresponse()
            if response.status in (401, 403):
                raise ValueError('knowledge_access_denied')
            if response.status == 404:
                raise ValueError('knowledge_reference_unavailable')
            if response.status != 200:
                raise KnowledgeUnavailable('knowledge_peer_unavailable')
            require(response.getheader('Content-Type', '').split(';', 1)[0].strip().lower() == 'application/json',
                    'knowledge_peer_media')
            chunks, size = [], 0
            while True:
                active_socket.settimeout(window.remaining())
                chunk = response.read1(min(65536, limit + 1 - size))
                size += len(chunk)
                window.consume(len(chunk))
                require(size <= limit, 'knowledge_response_limit')
                if not chunk:
                    break
                chunks.append(chunk)
                if response.isclosed():
                    break
            window.remaining()
            try:
                value = json.loads(b''.join(chunks).decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
                record = response_model.model_validate_json(json.dumps(value, allow_nan=False))
            except (ValueError, RecursionError):
                raise KnowledgeUnavailable('knowledge_peer_protocol') from None
            window.remaining()
            return record
        except (OSError, http.client.HTTPException):
            raise KnowledgeUnavailable('knowledge_peer_unavailable') from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
