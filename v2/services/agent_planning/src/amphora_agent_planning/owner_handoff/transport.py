"""Compiled owner calls with bounded exchange time and explicit uncertainty."""

import http.client
import json
import math
import socket
import threading
import time
from urllib.parse import urlsplit

from amphora_contracts_core import Identifier
from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AcceptedGraphChange,
    GraphChangeDecision,
)
from pydantic import TypeAdapter

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..publication.records import encode
from .request import MODELS, OwnerRequest


class OwnerUnavailable(ValueError):
    """Unknown or unusable response; never proof of absence or safe new identity."""


class OwnerDenied(ValueError):
    """Authentication or authorization denied this exchange."""


class OwnerAbsent(ValueError):
    """An exact read reported absence; not permission to submit without fresh rights."""


class OwnerConflict(ValueError):
    """The peer rejected an identity/head; reconcile the original identity."""


class OwnerInvalid(ValueError):
    """A write was explicitly rejected as invalid, not scientifically accepted."""


class HandoffWindow:
    def __init__(self, seconds=20):
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 20, "handoff_deadline")
        self.deadline, self.calls, self.consumed = time.monotonic() + seconds, 0, 0

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise OwnerUnavailable("handoff_exchange_expired")
        return remaining

    def start(self):
        self.remaining()
        require(self.calls < 4, "handoff_exchange_limit")
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        require(self.consumed <= 4194304, "handoff_response_total_limit")


class OwnerTransport:
    def __init__(self, owner_id, owner, endpoint, token):
        TypeAdapter(Identifier).validate_python(owner_id, strict=True)
        require(owner in {"research", "knowledge"}, "handoff_owner")
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, "handoff_endpoint")
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and
                parsed.port is not None and 1 <= parsed.port <= 65535 and parsed.username is None and
                parsed.password is None and parsed.path in ("", "/") and not parsed.query and
                not parsed.fragment and not any(c.isspace() for c in endpoint))
        except ValueError:
            valid = False
        require(valid, "handoff_endpoint")
        require(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(c) <= 126 for c in token), "handoff_credential")
        self.owner_id, self.owner = owner_id, owner
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def _bind(self, request):
        require(type(request) is OwnerRequest and request.owner == self.owner and
            request.selection.document()["owner_id"] == self.owner_id, "handoff_owner_binding")
        require(OwnerRequest.bind(request.selection, request.document()).canonical == request.canonical, "handoff_request_canonical")

    def read(self, request, window, *, guard=None):
        self._bind(request)
        method, path, body, model, limit = request.read_call()
        require(body is None or len(body) <= 4096, "handoff_reference_limit")
        return self._exchange(method, path, body, model, limit, window, False, guard)

    def submit(self, request, window, *, guard=None):
        self._bind(request)
        model = GraphChangeDecision if request.kind == "graph" else MODELS[request.kind]
        return self._exchange("POST", request.submit_path(), request.canonical, model, 262144, window, True, guard)

    def accepted(self, request, reference, window, *, guard=None):
        self._bind(request)
        require(request.kind == "graph", "handoff_receipt_kind")
        reference = AcceptedChangeRef.model_validate_json(reference.model_dump_json(warnings=False))
        proposal = request.document()
        require(reference.graph == proposal.graph and reference.change_id == proposal.change_id, "handoff_accepted_reference")
        body = encode(reference.model_dump(mode="json"))
        require(len(body) <= 4096, "handoff_reference_limit")
        return self._exchange("POST", "/v1/graph-changes/read", body, AcceptedGraphChange, 1048576, window, False, guard)

    def _exchange(self, method, path, body, model, limit, window, write, guard):
        window.start()
        if guard is not None:
            guard()
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
            if guard is not None:
                guard()
            connection.request(method, path, body, {"Authorization": "Bearer " + self._token, "Content-Type": "application/json"})
            active_socket.settimeout(window.remaining())
            response = connection.getresponse()
            if response.status in {401, 403}:
                raise OwnerDenied("handoff_access_denied")
            if response.status == 404:
                if write:
                    raise OwnerUnavailable("handoff_dependency_unavailable")
                raise OwnerAbsent("handoff_reference_absent")
            if response.status == 409:
                raise OwnerConflict("handoff_identity_conflict")
            if write and response.status in {400, 413, 415, 422}:
                raise OwnerInvalid("handoff_request_rejected")
            if response.status != 200:
                raise OwnerUnavailable("handoff_write_uncertain" if write else "handoff_read_unavailable")
            require(response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() == "application/json", "handoff_response_media")
            chunks, size = [], 0
            while True:
                active_socket.settimeout(window.remaining())
                chunk = response.read1(min(65536, limit + 1 - size))
                size += len(chunk)
                window.consume(len(chunk))
                require(size <= limit, "handoff_response_limit")
                if not chunk:
                    break
                chunks.append(chunk)
                if response.isclosed():
                    break
            window.remaining()
            try:
                value = json.loads(b"".join(chunks).decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
                record = model.model_validate_json(json.dumps(value, allow_nan=False))
            except (ValueError, RecursionError):
                raise OwnerUnavailable("handoff_response_protocol") from None
            window.remaining()
            return record
        except (OSError, http.client.HTTPException):
            raise OwnerUnavailable("handoff_write_uncertain" if write else "handoff_read_unavailable") from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
