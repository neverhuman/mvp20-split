"""Explicit loopback peers, bounded reads and safe failure classification."""

import http.client
import json
import math
import socket
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from ..authoring.canonical import KnowledgeError


class PeerUnavailable(KnowledgeError):
    """Transient/ambiguous observation; retain pending intent for exact retry."""


@dataclass
class ReadBudget:
    seconds: float = 20
    max_calls: int = 512
    max_bytes: int = 32 * 1024 * 1024
    deadline: float = field(init=False)
    calls: int = field(default=0, init=False)
    consumed: int = field(default=0, init=False)

    def __post_init__(self):
        if (type(self.seconds) not in (int, float) or not math.isfinite(self.seconds)
                or not 0 < self.seconds <= 30 or type(self.max_calls) is not int
                or not 1 <= self.max_calls <= 1024 or type(self.max_bytes) is not int
                or not 1 <= self.max_bytes <= 64 * 1024 * 1024):
            raise ValueError("invalid_read_budget")
        self.deadline = time.monotonic() + self.seconds

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise PeerUnavailable("peer_deadline")
        return min(5, remaining)

    def start(self):
        self.remaining()
        if self.calls >= self.max_calls:
            raise KnowledgeError("peer_call_limit")
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        if self.consumed > self.max_bytes:
            raise KnowledgeError("peer_total_bytes_limit")


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("nonfinite")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=constant)
    except (ValueError, RecursionError) as error:
        raise PeerUnavailable("peer_protocol_error") from error


class PeerTransport:
    def __init__(self, endpoint, token):
        if not isinstance(endpoint, str) or not 1 <= len(endpoint) <= 512:
            raise ValueError("explicit_loopback_peer_required")
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                and parsed.port is not None and 1 <= parsed.port <= 65535
                and parsed.username is None and parsed.password is None
                and parsed.path in ("", "/") and not parsed.query and not parsed.fragment)
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("explicit_loopback_peer_required")
        if (not isinstance(token, str) or not 32 <= len(token) <= 512
                or any(not 33 <= ord(char) <= 126 for char in token)):
            raise ValueError("invalid_peer_credential")
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def read(self, path, budget, *, body=None, limit=262144, json_body=True):
        budget.start()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=budget.remaining())
        timer = None
        try:
            connection.connect()
            active_socket = connection.sock

            def expire():
                try:
                    active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            # A socket timeout alone is an inactivity limit, not a whole-response
            # deadline. Interrupt trickling headers/bodies at the review deadline.
            timer = threading.Timer(max(0, budget.deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            headers = {"Authorization": "Bearer " + self._token}
            if body is not None:
                headers["Content-Type"] = "application/json"
            connection.request("GET" if body is None else "POST", path, body=body, headers=headers)
            active_socket.settimeout(budget.remaining())
            response = connection.getresponse()
            if response.status in (401, 403):
                raise KnowledgeError("peer_access_denied")
            if response.status == 404:
                raise KnowledgeError("reference_unavailable")
            if response.status != 200:
                raise PeerUnavailable("peer_unavailable")
            if json_body and response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise PeerUnavailable("peer_protocol_error")
            chunks, size = [], 0
            while True:
                # read1 performs at most one underlying read; reset timeout to the
                # remaining whole-review budget, not a fresh timeout per chunk.
                active_socket.settimeout(budget.remaining())
                block = response.read1(min(65536, limit + 1 - size))
                budget.consume(len(block))
                size += len(block)
                if size > limit:
                    raise KnowledgeError("peer_response_limit")
                if not block:
                    break
                chunks.append(block)
                if response.isclosed():
                    break
            return b"".join(chunks)
        except (OSError, http.client.HTTPException) as error:
            raise PeerUnavailable("peer_unavailable") from error
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()

    def record(self, path, model, budget, *, query=None):
        raw = self.read(path, budget, body=None if query is None else query.model_dump_json().encode())
        value = strict_json(raw)
        try:
            return model.model_validate_json(json.dumps(value, allow_nan=False))
        except (ValueError, RecursionError) as error:
            raise PeerUnavailable("peer_protocol_error") from error
