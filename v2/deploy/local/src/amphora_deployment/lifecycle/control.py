"""Authenticated loopback control; commands cannot supply executable/configuration data."""

import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from ..profile import ProfileError, require


class ControlServer(HTTPServer):
    def __init__(self, port, supervisor, token):
        require(type(token) is str and 32 <= len(token) <= 256 and token.isascii(), "lifecycle_control_token")
        require(type(port) is int and 0 <= port <= 65535, "lifecycle_control_port")
        self.supervisor, self._token, self.stopping = supervisor, token, False
        super().__init__(("127.0.0.1", port), ControlHandler)
        self.timeout = .25

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(3)
        return connection, address

    def serve(self):
        try:
            while not self.stopping:
                self.handle_request()
                if not self.stopping:
                    self.supervisor.tick()
        finally:
            self.server_close()

    def handle_error(self, request, client_address):
        # Base server diagnostics can print raw request/exception data.
        pass


class ControlHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _respond(self, status, record):
        raw = json.dumps(record, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self):
        provided = self.headers.get_all("Authorization", [])
        expected = "Bearer " + self.server._token
        if len(provided) != 1 or not hmac.compare_digest(provided[0].encode(), expected.encode()):
            self._respond(401, {"error": "control_unauthorized"})
            return False
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            self._respond(400, {"error": "control_body_not_allowed"})
            return False
        return True

    def do_GET(self):
        if not self._authorized():
            return
        if self.path != "/status":
            self._respond(404, {"error": "control_route_unknown"})
            return
        record = {"owners": self.server.supervisor.status()}
        if self.server.supervisor.workers.slots:
            record["workers"] = self.server.supervisor.workers.status()
        self._respond(200, record)

    def do_POST(self):
        if not self._authorized():
            return
        parts = self.path.split("/")
        try:
            if self.path == "/shutdown":
                self.server.supervisor.close()
                self.server.stopping = True
                result = {"state": "stopping"}
            elif len(parts) == 4 and parts[:2] == ["", "owners"] and parts[3] in {"start", "restart", "drain", "force-stop"}:
                operation = getattr(self.server.supervisor, parts[3].replace("-", "_"))
                result = operation(parts[2])
            elif len(parts) == 4 and parts[:2] == ["", "workers"] and parts[3] in {"start", "quiesce", "recover", "force-stop"}:
                result = self.server.supervisor.worker_command(parts[2], parts[3])
            else:
                self._respond(404, {"error": "control_route_unknown"})
                return
        except ProfileError as error:
            self._respond(409, {"error": str(error)})
            return
        except Exception:  # noqa: BLE001 - control never exposes private child diagnostics.
            self._respond(503, {"error": "control_operation_failed"})
            return
        self._respond(200, result)
