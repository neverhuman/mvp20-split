"""Actual loopback checks for test instrumentation; not production owner evidence."""

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError

import pytest

spec = importlib.util.spec_from_file_location("worker_test_support", Path(__file__).with_name("support.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def test_relay_preserves_real_operation_then_drops_only_response():
    operations = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            operations.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

        def do_GET(self):
            body = json.dumps(operations).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    relay = support.FaultRelay(f"http://127.0.0.1:{server.server_port}")
    payload = {"identity": {"command_id": "original"}, "payload": {"value": 1}}
    try:
        relay.drop_path = "/v1/command"
        with pytest.raises((URLError, ConnectionError)):
            support.request(relay.endpoint, "/v1/command", "fixture-token", payload)
        assert support.decoded(relay.endpoint, "/v1/history", "fixture-token") == [payload]
        assert operations == [payload]
        assert relay.events[0]["fault"] == "response_dropped_after_owner_success"
        assert "token" not in json.dumps(relay.events)
    finally:
        relay.close()
        server.shutdown()
        server.server_close()
        thread.join(5)
