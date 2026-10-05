"""Configured supervisor-only owner transport; read-only POST is not a write retry."""

import http.client
import json
import socket
import threading
from urllib.parse import urlsplit

from amphora_contracts_core import Identifier, Scope
from pydantic import TypeAdapter

from ..supervision_capture.reader import constant, unique
from ..supervision_scope.observations import require
from .window import (
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeInvalid,
    ExchangeUnavailable,
)


class SupervisorTransport:
    def __init__(self, actor_id, scope, endpoint, token):
        TypeAdapter(Identifier).validate_python(actor_id, strict=True)
        self.actor_id, self.scope = actor_id, Scope.model_validate_json(scope.model_dump_json())
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, 'supervisor_endpoint')
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and parsed.port is not None and
                1 <= parsed.port <= 65535 and parsed.username is None and parsed.password is None and
                parsed.path in ('', '/') and not parsed.query and not parsed.fragment and
                not any(c.isspace() for c in endpoint))
        except ValueError:
            valid = False
        require(valid, 'supervisor_endpoint')
        require(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(c) <= 126 for c in token), 'supervisor_credential')
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def _exchange(self, method, path, body, model, window, *, write=False, guard=None):
        require(not write or method == 'POST' and callable(guard), 'supervisor_write_guard_required')
        window.start()
        if write:
            guard()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=min(window.remaining(), 5))
        timer = None
        try:
            connection.connect()
            active = connection.sock

            def expire():
                try:
                    active.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(window.remaining(), expire)
            timer.daemon = True
            timer.start()
            if write:
                guard()
            window.remaining()
            connection.request(method, path, body, {'Authorization': 'Bearer ' + self._token,
                                                    'Content-Type': 'application/json'})
            active.settimeout(min(window.remaining(), 5))
            response = connection.getresponse()
            if response.status in {401, 403}:
                raise ExchangeDenied('supervisor_denied')
            if response.status == 404:
                if write:
                    raise ExchangeUnavailable('supervisor_dependency_unavailable')
                raise ExchangeAbsent('supervisor_read_absent')
            if response.status == 409:
                raise ExchangeConflict('supervisor_identity_conflict')
            if response.status in {400, 413, 415, 422}:
                raise ExchangeInvalid('supervisor_request_rejected')
            if response.status != 200:
                raise ExchangeUnavailable('supervisor_write_uncertain' if write else 'supervisor_read_unavailable')
            if (response.getheader('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json' or
                    response.getheader('Content-Encoding', 'identity') != 'identity'):
                raise ExchangeUnavailable('supervisor_response_media')
            chunks, size = [], 0
            while True:
                active.settimeout(min(window.remaining(), 5))
                block = response.read1(min(65536, 262145 - size))
                size += len(block)
                window.consume(len(block))
                if size > 262144:
                    raise ExchangeUnavailable('supervisor_response_limit')
                if not block:
                    break
                chunks.append(block)
                if response.isclosed():
                    break
            try:
                value = json.loads(b''.join(chunks), object_pairs_hook=unique, parse_constant=constant)
                record = model.model_validate_json(json.dumps(value, allow_nan=False))
            except (ValueError, RecursionError):
                raise ExchangeUnavailable('supervisor_response_protocol') from None
            window.remaining()
            return record
        except (OSError, http.client.HTTPException):
            raise ExchangeUnavailable('supervisor_write_uncertain' if write else 'supervisor_read_unavailable') from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
