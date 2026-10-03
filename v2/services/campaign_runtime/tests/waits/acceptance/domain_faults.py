"""Suppress actual successful HTTP acknowledgements; never simulate owner commits."""
import hashlib
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from amphora_tool_protocol import HttpTransport


class LostAcknowledgement:
    def __init__(self, endpoint, target):
        self.events, self.target, self.lost = [], target, False
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                reply = HttpTransport(endpoint, token).request("POST", self.path, body)
                event = {"path":self.path,"command_sha256":hashlib.sha256(body).hexdigest(),
                         "command":json.loads(body),"response":json.loads(reply.body),"status":reply.status}
                owner.events.append(event)
                status, content = reply.status, reply.body
                if self.path == owner.target and status == 200 and not owner.lost:
                    owner.lost = True
                    event["acknowledgement_suppressed"] = True
                    status, content = 503, b'{"reason_code":"test_acknowledgement_suppressed"}'
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        self.server = ThreadingHTTPServer(("127.0.0.1",0),Handler)
        self.server.daemon_threads = True
        self.endpoint = "http://127.0.0.1:" + str(self.server.server_port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)


class DomainFaults:
    def __init__(self, runtime, data):
        self.runtime, self.data = runtime, data
        self.relay = LostAcknowledgement(data,"/v1/reservations/confirm")
        self.evidence = {}

    def accept(self, command):
        runtime = self.runtime
        relay = LostAcknowledgement(runtime.endpoint,"/v1/graph-receipts")
        try:
            transport = HttpTransport(relay.endpoint,"j"*32)
            body = json.dumps(command).encode()
            first = transport.request("POST","/v1/graph-receipts",body)
            assert first.status == 503 and relay.lost
            committed = relay.events[0]["response"]
            assert committed["outcome"]["status"] == "accepted", committed
            closure = runtime.runtime.request(runtime.wait_path)
            runtime._start()
            assert runtime.runtime.request(runtime.wait_path) == closure
            replay = transport.request("POST","/v1/graph-receipts",body)
            assert replay.status == 200 and json.loads(replay.body) == committed
            assert relay.events[0]["command_sha256"] == relay.events[1]["command_sha256"]
            self.evidence["receipt"] = {"caller_first_status":first.status,"events":relay.events,
                                         "closure_preserved_after_process_replacement":True}
            return committed
        finally:
            relay.close()

    def confirm(self, report):
        runtime = self.runtime
        self.relay.lost = False
        start = len(self.relay.events)
        unrelated = []
        for _ in range(32):
            failed = runtime.deliver(limit=1)
            if self.relay.lost:
                break
            unrelated.append(failed)
        assert failed["failed"] == 1 and failed["acknowledged"] == 0 and self.relay.lost, (failed,self.relay.events[start:])
        before = runtime.runtime.request(runtime.wait_path)
        runtime._start()
        assert runtime.runtime.request(runtime.wait_path) == before
        deadline = time.monotonic() + 10
        while True:
            delivered = runtime.deliver()
            if delivered["acknowledged"]:
                break
            assert time.monotonic() < deadline, delivered
            time.sleep(0.25)
        assert delivered["acknowledged"] == 1
        events = self.relay.events[start:]
        assert len(events) == 2 and events[0]["command_sha256"] == events[1]["command_sha256"], events
        assert events[0]["response"] == events[1]["response"]
        assert events[1]["response"]["outcome"]["status"] == "confirmed"
        artifact = report["artifact"]
        content = HttpTransport(self.data,"t"*32).request("GET","/v1/artifacts/"+artifact["artifact_id"]+"/content")
        assert content.status == 200 and hashlib.sha256(content.body).hexdigest() == artifact["sha256"]
        self.evidence["confirmation"] = {"first_delivery":failed,"retry":delivered,"events":events,
                                           "other_delivery_passes":unrelated,
                                           "artifact_bytes_sha256":hashlib.sha256(content.body).hexdigest()}
        return delivered

    def close(self):
        self.relay.close()
