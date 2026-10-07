"""Local static hosting, browser sessions and bounded public owner proxy."""

from http.cookies import SimpleCookie, CookieError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import threading
import uuid

from .configuration import GatewayError, require, unique
from .proxy import Route, forward, MAXIMUM_BODY
from .sessions import Sessions, SessionDenied


COOKIE = "amphora_local_session"


class GatewayServer(ThreadingHTTPServer):
    # Cooperative close joins accepted requests. A stalled request is reported by
    # the external drain deadline; only an explicit force-stop may terminate it.
    daemon_threads = False

    def __init__(self, configuration, port):
        self.configuration = configuration
        self.sessions = Sessions()
        self.slots = threading.BoundedSemaphore(16)
        self.assets = {}
        for path, name, content_type in (("/", "index.html", "text/html; charset=utf-8"),
                                        ("/app.js", "app.js", "text/javascript; charset=utf-8"),
                                        ("/app.css", "app.css", "text/css; charset=utf-8")):
            with (configuration.public_directory / name).open("rb") as stream:
                raw = stream.read(16777217)
            require(len(raw) <= 16777216, "gateway_asset_bound")
            self.assets[path] = (content_type, raw)
        super().__init__(("127.0.0.1", port), GatewayHandler)
        self.origin = "http://127.0.0.1:" + str(self.server_port)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(20)
        return connection, address

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        pass  # Never dump request headers, body or raw transport diagnostics.


class GatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, status, content_type, raw, *, cookie=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header("Connection", "close")
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def json(self, status, value, *, cookie=None):
        self.respond(status, "application/json", json.dumps(value, separators=(",", ":")).encode(), cookie=cookie)

    def boundary(self, *, unsafe):
        hosts = self.headers.get_all("Host", [])
        require(hosts == ["127.0.0.1:" + str(self.server.server_port)], "gateway_host_denied")
        if unsafe:
            require(self.headers.get_all("Origin", []) == [self.server.origin], "gateway_origin_denied")
        require(not self.headers.get_all("Transfer-Encoding"), "gateway_transfer_encoding")

    def body(self, maximum=MAXIMUM_BODY):
        lengths = self.headers.get_all("Content-Length", [])
        require(len(lengths) <= 1, "gateway_body_length")
        length = lengths[0] if lengths else "0"
        require(length.isdecimal() and int(length) <= maximum, "gateway_body_bound")
        size = int(length)
        if size:
            require(self.headers.get("Content-Type", "").split(";")[0] == "application/json", "gateway_body_type")
        raw = self.rfile.read(size)
        require(len(raw) == size, "gateway_body_truncated")
        return raw

    def session(self):
        values = self.headers.get_all("Cookie", [])
        require(len(values) <= 1, "gateway_cookie_denied")
        raw = values[0] if values else ""
        require(len(raw) <= 4096, "gateway_cookie_denied")
        cookie = SimpleCookie()
        try:
            cookie.load(raw)
            token = cookie[COOKIE].value
        except (CookieError, KeyError):
            raise SessionDenied("session_denied") from None
        self.server.sessions.authenticate(token)
        return token

    def proxy(self, method, body):
        route = Route.parse(self.path)
        peer = self.server.configuration.peers.get(route.owner)
        if peer is None:
            self.json(503, {"error":"owner_not_configured"})
            return
        try:
            status, content_type, raw = forward(peer, route, method, body, uuid.uuid4().hex)
        except GatewayError:
            self.json(502, {"error":"owner_unavailable"})
            return
        self.respond(status, content_type, raw)

    def do_GET(self):
        try:
            self.boundary(unsafe=False)
            require(not self.body(), "gateway_get_body")
            if self.path in self.server.assets:
                content_type, raw = self.server.assets[self.path]
                self.respond(200, content_type, raw)
                return
            self.session()
            if self.path == "/session":
                self.json(200, self.server.configuration.context)
            else:
                self.proxy("GET", b"")
        except SessionDenied:
            self.json(401, {"error":"session_required"})
        except GatewayError:
            self.json(502 if self.path.startswith("/api/") else 400, {"error":"gateway_request_failed"})
        except Exception:
            self.json(503, {"error":"gateway_unavailable"})

    def do_POST(self):
        try:
            launcher = self.path == "/launcher/ticket"
            self.boundary(unsafe=not launcher)
            if launcher:
                expected = "Bearer " + self.server.configuration.launcher_key
                values = self.headers.get_all("Authorization", [])
                require(len(values) == 1 and hmac.compare_digest(values[0].encode(), expected.encode()), "gateway_launcher_denied")
                require(not self.body(), "gateway_launcher_body")
                self.json(200, {"ticket":self.server.sessions.issue_ticket()})
            elif self.path == "/session":
                record = json.loads(self.body(4096), object_pairs_hook=unique)
                require(type(record) is dict and set(record) == {"ticket"}, "gateway_ticket_shape")
                token = self.server.sessions.exchange(record["ticket"])
                self.json(200, self.server.configuration.context,
                          cookie=COOKIE + "=" + token + "; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800")
            elif self.path == "/session/logout":
                require(not self.body(), "gateway_logout_body")
                self.server.sessions.revoke(self.session())
                self.json(200, {"status":"signed_out"}, cookie=COOKIE + "=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0")
            else:
                self.session()
                self.proxy("POST", self.body())
        except SessionDenied:
            self.json(401, {"error":"session_required"})
        except GatewayError:
            self.json(403, {"error":"gateway_request_denied"})
        except Exception:
            self.json(503, {"error":"gateway_unavailable"})
