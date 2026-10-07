import http.client
import http.server
import socket
import ssl
import threading
import time
from contextlib import contextmanager
from typing import ClassVar

import pytest
from amphora_deployment import ProfileError
from amphora_deployment.tool_access.identity import HOSTNAME
from amphora_deployment.tool_access.proxy import OwnerRoute, ToolAccessServer

from .test_identity import pytestmark  # noqa: F401

TOKEN = "synthetic-tool-token-000000000000000000"


@contextmanager
def servers(identity, handler, **settings):
    upstream = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    proxy = ToolAccessServer(
        identity, OwnerRoute("runtime", upstream.server_port), port=0, **settings
    )
    threads = [
        threading.Thread(target=server.serve_forever) for server in (upstream, proxy)
    ]
    for thread in threads:
        thread.start()
    try:
        yield proxy, upstream
    finally:
        for server in (proxy, upstream):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(6)
            assert not thread.is_alive()


def connection(identity, port):
    raw = socket.create_connection(("127.0.0.1", port), timeout=3)
    context = ssl.create_default_context(cafile=str(identity.certificate))
    secured = context.wrap_socket(raw, server_hostname=HOSTNAME)
    client = http.client.HTTPConnection(HOSTNAME, port, timeout=3)
    client.sock = secured
    return client


class Owner(http.server.BaseHTTPRequestHandler):
    observed: ClassVar[list] = []

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.observed.append((self.path, raw, dict(self.headers)))
        self.send_response(
            200 if self.headers.get("Authorization") == "Bearer " + TOKEN else 403
        )
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b'{"owner":true}')))
        self.end_headers()
        self.wfile.write(b'{"owner":true}')

    def log_message(self, *_args):
        pass


def test_exact_body_and_original_authority_go_only_to_fixed_owner(identity):
    Owner.observed = []
    with servers(identity, Owner) as (proxy, _upstream):
        assert proxy.server_address[0] == "127.0.0.1"
        client = connection(identity, proxy.server_port)
        client.request(
            "POST",
            "/v1/commands",
            body=b'{"fixture":true}',
            headers={
                "Authorization": "Bearer " + TOKEN,
                "Content-Type": "application/json",
                "Cookie": "never-forward",
            },
        )
        response = client.getresponse()
        assert response.status == 200 and response.read() == b'{"owner":true}'
        client.close()
        path, body, headers = Owner.observed[-1]
        assert path == "/v1/commands" and body == b'{"fixture":true}'
        assert headers["Authorization"] == "Bearer " + TOKEN and "Cookie" not in headers
        client = connection(identity, proxy.server_port)
        client.request(
            "POST",
            "/v1/commands",
            body=b"",
            headers={"Authorization": "Bearer " + "x" * 40},
        )
        assert client.getresponse().status == 403
        client.close()


@pytest.mark.parametrize(
    "fault,status",
    [
        ("path", 400),
        ("host", 400),
        ("auth", 401),
        ("media", 415),
        ("length", 413),
        ("chunked", 400),
        ("duplicate_length", 400),
    ],
)
def test_invalid_input_never_reaches_owner(identity, fault, status):
    Owner.observed = []
    with servers(identity, Owner) as (proxy, _upstream):
        client = connection(identity, proxy.server_port)
        client.putrequest(
            "POST", "/outside" if fault == "path" else "/v1/commands", skip_host=True
        )
        client.putheader(
            "Host",
            "foreign" if fault == "host" else HOSTNAME + ":" + str(proxy.server_port),
        )
        if fault != "auth":
            client.putheader("Authorization", "Bearer " + TOKEN)
        if fault == "media":
            client.putheader("Content-Type", "text/html")
        if fault == "length":
            client.putheader("Content-Length", "16777217")
        if fault == "chunked":
            client.putheader("Transfer-Encoding", "chunked")
        if fault == "duplicate_length":
            client.putheader("Content-Length", "0")
            client.putheader("Content-Length", "0")
        client.endheaders()
        response = client.getresponse()
        assert response.status == status and response.read() == b""
        client.close()
        assert not Owner.observed


def test_header_stall_is_bounded_by_absolute_deadline(identity, monkeypatch):
    monkeypatch.setattr("amphora_deployment.tool_access.proxy.DEADLINE_SECONDS", 0.2)
    with servers(identity, Owner) as (proxy, _upstream):
        client = connection(identity, proxy.server_port)
        started = time.monotonic()
        client.sock.sendall(b"POST /v1/commands HTTP/1.1\r\nHost: ")
        assert client.sock.recv(100) == b""
        assert time.monotonic() - started < 2
        client.close()


def test_route_cannot_select_arbitrary_host_or_owner():
    with pytest.raises(ProfileError):
        OwnerRoute("planning", 8080)
    with pytest.raises(ProfileError):
        OwnerRoute("runtime", True)


def test_response_limit_returns_uncertainty_instead_of_truncating_success(
    identity, monkeypatch
):
    monkeypatch.setattr("amphora_deployment.tool_access.proxy.MAX_BODY", 8)
    with servers(identity, Owner) as (proxy, _upstream):
        client = connection(identity, proxy.server_port)
        client.request(
            "POST",
            "/v1/commands",
            body=b"",
            headers={"Authorization": "Bearer " + TOKEN},
        )
        response = client.getresponse()
        assert response.status == 502 and response.read() == b""
        assert proxy.diagnostics.snapshot()['failures'] == {'response_headers.oversized': 1}
        client.close()


def test_partial_upstream_response_is_not_forwarded_as_success(identity):
    class TruncatedOwner(Owner):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Length", "100")
            self.end_headers()
            self.wfile.write(b"partial")

    with servers(identity, TruncatedOwner) as (proxy, _upstream):
        client = connection(identity, proxy.server_port)
        client.request(
            "POST",
            "/v1/commands",
            body=b"",
            headers={"Authorization": "Bearer " + TOKEN},
        )
        response = client.getresponse()
        assert response.status == 502 and response.read() == b""
        assert proxy.diagnostics.snapshot()['failures'] == {'response_body.truncated': 1}
        client.close()


def test_transport_drain_waits_for_accepted_owner_response(identity):
    entered, release, closed = threading.Event(), threading.Event(), threading.Event()

    class WaitingOwner(Owner):
        def do_POST(self):
            entered.set()
            assert release.wait(5)
            super().do_POST()

    result = []
    with servers(identity, WaitingOwner) as (proxy, _upstream):

        def call():
            client = connection(identity, proxy.server_port)
            try:
                client.request(
                    "POST",
                    "/v1/commands",
                    body=b"",
                    headers={"Authorization": "Bearer " + TOKEN},
                )
                response = client.getresponse()
                result.append((response.status, response.read()))
            finally:
                client.close()

        caller = threading.Thread(target=call)
        caller.start()
        assert entered.wait(3)

        def drain():
            proxy.shutdown()
            proxy.server_close()
            closed.set()

        closer = threading.Thread(target=drain)
        closer.start()
        try:
            assert not closed.wait(0.2)
        finally:
            release.set()
            caller.join(5)
            closer.join(5)
        assert closed.is_set() and result == [(200, b'{"owner":true}')]
