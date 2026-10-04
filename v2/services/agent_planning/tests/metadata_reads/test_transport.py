import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.metadata_reads import MetadataTransport, MetadataWindow
from amphora_agent_planning.metadata_reads.targets import target
from amphora_agent_planning.registry_access import DiscoveryQuery, RegistryReader
from amphora_contracts_tools import ReleasePage

from ..campaign_context.test_selection import request
from ..registry_access.test_discovery import record


@pytest.fixture
def server():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            self.server.calls.append((self.path, self.headers.get("Authorization")))
            try:
                self.send_response(self.server.status)
                self.send_header("Content-Type", self.server.media)
                self.send_header("Content-Length", str(len(self.server.body)))
                self.end_headers()
                if self.server.slow:
                    for byte in self.server.body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.03)
                else:
                    self.wfile.write(self.server.body)
            except OSError:
                pass
    host = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    host.daemon_threads = True
    host.status, host.media, host.calls, host.slow = 200, "application/json", [], False
    host.body = ReleasePage(items=(record(),), next_after=None).model_dump_json().encode()
    thread = threading.Thread(target=host.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield host, MetadataTransport("registry", f"http://127.0.0.1:{host.server_port}", "t" * 32)
    host.shutdown()
    host.server_close()
    thread.join(2)


def test_actual_get_authentication_body_and_exact_selected_release(server):
    host, transport = server
    reader = RegistryReader(transport)
    result = reader.discover(DiscoveryQuery(request(), capability_id=record().lock.tool.capability_id))
    assert result.complete and result.records[0].document() == record()
    assert result.calls == 1 and result.bytes == len(host.body)
    assert host.calls == [("/v1/releases?limit=100&capability_id=" + record().lock.tool.capability_id, "Bearer " + "t" * 32)]
    host.body = record().model_dump_json().encode()
    assert reader.exact(request(), record().lock).document() == record()


@pytest.mark.parametrize("status,code", [(401, "denied"), (403, "denied"), (404, "missing"),
                                      (302, "unavailable"), (500, "unavailable")])
def test_non_success_is_safe_and_never_retried(server, status, code):
    host, transport = server
    host.status, host.body = status, b"SECRET"
    result = RegistryReader(transport).discover(DiscoveryQuery(request()))
    assert result.failure == "metadata_" + code and result.records == () and len(host.calls) == 1


@pytest.mark.parametrize("body", [b"{}", b"null", b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff"])
def test_malformed_body_is_not_metadata(server, body):
    host, transport = server
    host.body = body
    assert RegistryReader(transport).discover(DiscoveryQuery(request())).failure == "metadata_protocol"


def test_media_size_total_and_call_bounds(server):
    host, transport = server
    host.media = "text/html"
    assert RegistryReader(transport).discover(DiscoveryQuery(request())).failure == "metadata_media"
    host.media, host.body = "application/json", b" " * 4194305
    assert RegistryReader(transport).discover(DiscoveryQuery(request())).failure == "metadata_response_limit"
    host.body = ReleasePage(items=(), next_after=None).model_dump_json().encode()
    window = MetadataWindow("registry")
    window.consumed = 16777216
    assert RegistryReader(transport).discover(DiscoveryQuery(request()), window).failure == "metadata_byte_limit"
    window = MetadataWindow("registry")
    window.calls = 8
    count = len(host.calls)
    assert RegistryReader(transport).discover(DiscoveryQuery(request()), window).failure == "metadata_call_limit"
    assert len(host.calls) == count


def test_trickling_body_cannot_extend_total_deadline(server):
    host, transport = server
    host.slow = True
    start = time.monotonic()
    result = RegistryReader(transport).discover(DiscoveryQuery(request()), MetadataWindow("registry", seconds=0.15))
    assert result.failure in {"metadata_deadline", "metadata_unavailable"} and not result.records
    assert time.monotonic() - start < 2


@pytest.mark.parametrize("path", ["https://remote.invalid/v1/releases?limit=1", "/v1/registry/activate",
    "/v1/releases?limit=1&limit=2", "/v1/releases?limit=0", "/v1/releases?limit=101", "/v1/releases?limit=1&sql=x",
    "/v1/releases?limit=1&after=bad", "/v1/releases?limit=1&capability_id=x%26y", "/v1/releases?limit=1&release=bad",
    "/v1/releases/" + "a" * 64 + "?ignored=1", "/v1/releases?limit=1#fragment"])
def test_arbitrary_route_or_query_cannot_trigger_io(server, path):
    host, transport = server
    with pytest.raises(ValueError):
        transport.read(path, MetadataWindow("registry"))
    assert host.calls == []


@pytest.mark.parametrize("endpoint", ["https://127.0.0.1:1", "http://localhost:1", "http://127.0.0.1",
    "http://user:pass@127.0.0.1:1", "http://127.0.0.1:1/other", "http://127.0.0.1:999999", "http://127.0.0.1:1?x=y"])
def test_configured_origin_is_loopback_only(endpoint):
    with pytest.raises(ValueError, match="metadata_endpoint"):
        MetadataTransport("registry", endpoint, "t" * 32)


def test_compiled_runtime_metadata_routes_cannot_read_registry():
    assert target("runtime", "/v1/definition-universe").__name__ == "DefinitionUniverse"
    assert target("runtime", "/v1/definition-schemas/" + "a" * 64 + "?schema_id=fixture&version=1&universe_sha256=" + "b" * 64).__name__ == "DefinitionSchema"
    for path in ("/v1/releases?limit=1", "/v1/definition-universe?extra=1",
                 "/v1/definition-schemas/" + "a" * 64 + "?schema_id=fixture&version=2&universe_sha256=" + "b" * 64):
        with pytest.raises(ValueError):
            target("runtime", path)


def test_expired_window_wrong_owner_and_invalid_credentials(server):
    host, transport = server
    with pytest.raises(ValueError, match="metadata_window"):
        transport.read("/v1/releases?limit=1", MetadataWindow("runtime"))
    with pytest.raises(ValueError, match="metadata_credential"):
        MetadataTransport("registry", f"http://127.0.0.1:{host.server_port}", "bad\n")
    window = MetadataWindow("registry")
    window.deadline = 0
    assert RegistryReader(transport).discover(DiscoveryQuery(request()), window).failure == "metadata_deadline"
    assert host.calls == []
    for seconds in (True, 0, 31, float("nan")):
        with pytest.raises(ValueError, match="metadata_seconds"):
            MetadataWindow("registry", seconds)
