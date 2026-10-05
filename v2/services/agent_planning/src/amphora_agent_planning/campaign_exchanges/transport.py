"""Guarded HTTP framing adapted from the existing bounded owner handoff transport."""

import http.client
import json
import socket
import threading
from urllib.parse import urlsplit

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .window import (
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeInvalid,
    ExchangeUnavailable,
)


class CompilerTransport:
    def __init__(self, owner, owner_id, actor_id, endpoint, token):
        require(owner in {'runtime', 'registry'}, 'compiler_owner')
        for value in (owner_id, actor_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, 'compiler_endpoint')
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and
                parsed.port is not None and 1 <= parsed.port <= 65535 and parsed.username is None and
                parsed.password is None and parsed.path in ('', '/') and not parsed.query and not parsed.fragment and
                not any(c.isspace() for c in endpoint))
        except ValueError:
            valid = False
        require(valid, 'compiler_endpoint')
        require(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(c) <= 126 for c in token),
                'compiler_credential')
        self.owner, self.owner_id, self.actor_id = owner, owner_id, actor_id
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def _exchange(self, method, path, body, model, limit, window, *, guard=None):
        require(window.owner == self.owner, 'compiler_window_owner')
        write = method == 'POST'
        require(not write or callable(guard), 'compiler_write_guard_required')
        window.start()
        if guard is not None:
            guard()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=window.remaining())
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
            if guard is not None:
                guard()
            connection.request(method, path, body, {'Authorization': 'Bearer ' + self._token,
                                                    'Content-Type': 'application/json'})
            active.settimeout(window.remaining())
            response = connection.getresponse()
            if response.status in {401, 403}:
                raise ExchangeDenied('compiler_denied')
            if response.status == 404:
                if write:
                    raise ExchangeUnavailable('compiler_dependency_unavailable')
                raise ExchangeAbsent('compiler_read_absent')
            if response.status == 409:
                raise ExchangeConflict('compiler_identity_conflict')
            if write and response.status in {400, 413, 415, 422}:
                raise ExchangeInvalid('compiler_request_rejected')
            if response.status != 200:
                raise ExchangeUnavailable('compiler_write_uncertain' if write else 'compiler_read_unavailable')
            if response.getheader('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
                raise ExchangeUnavailable('compiler_response_media')
            chunks, size = [], 0
            while True:
                active.settimeout(window.remaining())
                part = response.read1(min(65536, limit + 1 - size))
                size += len(part)
                window.consume(len(part))
                if size > limit:
                    raise ExchangeUnavailable('compiler_response_limit')
                if not part:
                    break
                chunks.append(part)
                if response.isclosed():
                    break
            try:
                value = json.loads(b''.join(chunks).decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
                record = model.model_validate_json(json.dumps(value, allow_nan=False))
            except (ValueError, RecursionError):
                raise ExchangeUnavailable('compiler_response_protocol') from None
            window.remaining()
            return record
        except (OSError, http.client.HTTPException):
            raise ExchangeUnavailable('compiler_write_uncertain' if write else 'compiler_read_unavailable') from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
