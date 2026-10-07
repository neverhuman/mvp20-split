"""Bounded TLS forwarding to one fixed loopback owner; bearer authority stays upstream."""

import http.client
import http.server
import socket
import ssl
import threading
import time
from dataclasses import dataclass

from ..profile import require
from .identity import HOSTNAME
from .load import ConnectionLoad

MAX_BODY = 16 * 1024 * 1024
DEADLINE_SECONDS = 30


@dataclass(frozen=True)
class OwnerRoute:
    owner: str
    upstream_port: int

    def __post_init__(self):
        require(self.owner in {"runtime", "artifact"}, "tool_tls_owner")
        require(
            type(self.upstream_port) is int and 1 <= self.upstream_port <= 65535,
            "tool_tls_upstream_port",
        )


class ToolAccessServer(http.server.ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True
    allow_reuse_address = False

    def __init__(self, identity, route, *, port, maximum_connections=16):
        require(type(port) is int and 0 <= port <= 65535, "tool_tls_port")
        require(isinstance(route, OwnerRoute), "tool_tls_route")
        route = OwnerRoute(route.owner, route.upstream_port)
        require(
            type(maximum_connections) is int and 1 <= maximum_connections <= 16,
            "tool_tls_connections",
        )
        self.context = identity.server_context()
        self.route, self.load = route, ConnectionLoad(maximum_connections)
        super().__init__(("127.0.0.1", port), ToolAccessHandler)

    def process_request(self, request, client_address):
        if not self.load.acquire():
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.load.release()
            raise

    def process_request_thread(self, request, client_address):
        # The accepting thread never blocks on an untrusted TLS handshake.
        try:
            request.settimeout(5)
            with self.context.wrap_socket(request, server_side=True) as secured:
                super().process_request_thread(secured, client_address)
        except (OSError, ssl.SSLError):
            self.shutdown_request(request)
        finally:
            self.load.release()

    def handle_error(self, request, client_address):
        # Never emit tracebacks containing headers, payloads or credentials.
        pass


class ToolAccessHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.deadline = time.monotonic() + DEADLINE_SECONDS
        self._upstream_socket = None
        self._timer = threading.Timer(DEADLINE_SECONDS, self._expire)
        self._timer.daemon = True
        self._timer.start()

    def _expire(self):
        # Inactivity timeouts alone do not bound trickled HTTP headers/bodies.
        for connection in (self.connection, self._upstream_socket):
            if connection is not None:
                try:
                    connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def finish(self):
        try:
            super().finish()
        finally:
            self._timer.cancel()
            self._timer.join()

    def log_message(self, *_args):
        pass

    def _reply(self, status, body=b"", media_type="application/json"):
        self.close_connection = True
        self.send_response_only(status)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _remaining(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("tool_tls_deadline")
        return min(5, remaining)

    def _body(self, length, deadline):
        body = bytearray()
        while len(body) < length:
            self.connection.settimeout(self._remaining(deadline))
            chunk = self.rfile.read1(min(65536, length - len(body)))
            if not chunk:
                raise ConnectionError("tool_tls_incomplete_body")
            body.extend(chunk)
        return bytes(body)

    def _forward(self):
        deadline = self.deadline
        headers = self.headers
        hosts = headers.get_all("Host", [])
        expected = HOSTNAME + ":" + str(self.server.server_port)
        if hosts != [expected]:
            self._reply(400)
            return
        if (
            not self.path.startswith("/v1/")
            or len(self.path) > 8192
            or any(character in self.path for character in ("?", "#", "\\", "\r", "\n"))
        ):
            self._reply(400)
            return
        lengths = headers.get_all("Content-Length", [])
        if headers.get_all("Transfer-Encoding") or len(lengths) > 1:
            self._reply(400)
            return
        if lengths and (
            not lengths[0].isascii() or not lengths[0].isdigit() or len(lengths[0]) > 10
        ):
            self._reply(400)
            return
        length = int(lengths[0]) if lengths else 0
        if length > MAX_BODY:
            self._reply(413)
            return
        tokens = headers.get_all("Authorization", [])
        if (
            len(tokens) != 1
            or not tokens[0].startswith("Bearer ")
            or not 32 <= len(tokens[0][7:]) <= 512
        ):
            self._reply(401)
            return
        media = headers.get_all("Content-Type", ["application/json"])
        if len(media) != 1 or media[0] not in {
            "application/json",
            "application/octet-stream",
        }:
            self._reply(415)
            return
        upstream = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.route.upstream_port,
            timeout=self._remaining(deadline),
        )
        sent = False
        try:
            raw = self._body(length, deadline)
            upstream.timeout = self._remaining(deadline)
            upstream.connect()
            self._upstream_socket = upstream.sock
            upstream.sock.settimeout(self._remaining(deadline))
            upstream.request(
                self.command,
                self.path,
                body=raw,
                headers={
                    "Authorization": tokens[0],
                    "Content-Type": media[0],
                    "Connection": "close",
                },
            )
            if upstream.sock is not None:
                upstream.sock.settimeout(self._remaining(deadline))
            response = upstream.getresponse()
            expected_length = response.length
            if expected_length is not None and expected_length > MAX_BODY:
                self._reply(502)
                return
            body = bytearray()
            while not response.isclosed():
                remaining = self._remaining(deadline)
                if self._upstream_socket is not None:
                    self._upstream_socket.settimeout(remaining)
                chunk = response.read1(min(65536, MAX_BODY + 1 - len(body)))
                if not chunk:
                    break
                body.extend(chunk)
                if len(body) > MAX_BODY:
                    self._reply(502)
                    return
            if expected_length is not None and len(body) != expected_length:
                self._reply(502)
                return
            media_type = response.getheader("Content-Type", "application/json")
            if media_type not in {"application/json", "application/octet-stream"}:
                media_type = "application/octet-stream"
            self.connection.settimeout(self._remaining(deadline))
            sent = True
            self._reply(response.status, bytes(body), media_type)
        except (OSError, http.client.HTTPException):
            if not sent:
                self._reply(502)
        finally:
            upstream.close()

    do_GET = _forward
    do_POST = _forward
    do_PUT = _forward

    def handle_expect_100(self):
        self._reply(417)
        return False

    def send_error(self, code, message=None, explain=None):
        self._reply(code)  # No reflected path/header/diagnostic content.
