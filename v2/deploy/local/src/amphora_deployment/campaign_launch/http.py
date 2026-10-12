"""Narrow authenticated loopback launch surface; no process-control routes."""
import hmac
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlsplit

from amphora_contracts_campaign_launch import LaunchProfileCatalog

from .intent import LaunchError, LaunchIntent
from ..campaign_successor import http as successor_http

ERRORS = {'launch_scope_denied': 403, 'launch_request_conflict': 409, 'launch_slot_busy': 409,
    'launch_profile_mismatch': 422, 'launch_profile_limit': 422, 'launch_request_invalid': 422,
    'launch_receipt_unavailable': 404, 'launch_unavailable': 503}


class LaunchServer(HTTPServer):
    allow_reuse_address = False

    def __init__(self, port, token, actor_id, policy, journal, accepting, stop, *, recover=None):
        if (type(port) is not int or not 0 <= port <= 65535 or type(token) is not str
                or not 32 <= len(token) <= 256 or not token.isascii()
                or not all(32 < ord(c) < 127 for c in token)):
            raise LaunchError('launch_listener_configuration_invalid')
        self._token, self.actor_id, self.policy, self.journal = token, actor_id, policy, journal
        self.accepting, self.stop = accepting, stop
        self.recover = recover
        super().__init__(('127.0.0.1', port), LaunchHandler)
        self.timeout = .25

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(3)
        return connection, address

    def handle_error(self, request, client_address):
        pass

    def serve(self):
        try:
            while not self.stop.is_set():
                self.handle_request()
        finally:
            self.server_close()


class LaunchHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _respond(self, status, value):
        raw = json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(raw)

    def _authorize(self):
        values = self.headers.get_all('Authorization', [])
        if len(values) != 1 or not hmac.compare_digest(values[0].encode(), ('Bearer ' + self.server._token).encode()):
            self._respond(401, {'reason_code': 'launch_authentication_required'})
            return False
        return True

    def _route(self):
        parsed = urlsplit(self.path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            return None, None
        successor_route = successor_http.route(parsed.path)
        if successor_route[0] is not None:
            return successor_route
        if parsed.path in {'/v1/campaign-launches', '/v1/campaign-launch-profiles'}:
            return parsed.path, None
        parts = parsed.path.split('/')
        if len(parts) == 4 and parts[:3] == ['', 'v1', 'campaign-launches']:
            identity = unquote(parts[3])
            if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', identity):
                return '/v1/campaign-launches/receipt', identity
        return None, None

    def _body(self, post):
        lengths = self.headers.get_all('Content-Length', [])
        if self.headers.get_all('Transfer-Encoding') or len(lengths) > 1:
            raise LaunchError('launch_request_invalid')
        length = lengths[0] if lengths else '0'
        if not length.isascii() or not length.isdecimal() or len(length) > 7:
            raise LaunchError('launch_request_invalid')
        size = int(length)
        if size > 262144 or (not post and size != 0):
            raise LaunchError('launch_request_invalid')
        if post and self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            raise LaunchError('launch_request_invalid')
        raw = self.rfile.read(size) if size else b''
        if len(raw) != size:
            raise LaunchError('launch_request_invalid')
        return raw

    def _handle(self, post):
        if not self._authorize():
            return
        try:
            raw = self._body(post)
            route, request_id = self._route()
            if route and route.startswith(successor_http.ROOT) and successor_http.handle(self, route, request_id, post, raw):
                return
            if not post and route == '/v1/campaign-launch-profiles':
                catalog = LaunchProfileCatalog(scope=self.server.policy.view.scope, profiles=(self.server.policy.view,))
                return self._respond(200, catalog.model_dump(mode='json'))
            if not post and route == '/v1/campaign-launches/receipt':
                scope = self.server.policy.view.scope
                state = self.server.journal.get((scope.tenant_id, scope.project_id, self.server.actor_id, request_id))
                if state is None:
                    raise LaunchError('launch_receipt_unavailable')
                return self._respond(200, state.receipt().model_dump(mode='json'))
            if post and route == '/v1/campaign-launches':
                if not self.server.accepting():
                    raise LaunchError('launch_unavailable')
                intent = LaunchIntent.parse(raw)
                intent.authorize(self.server.actor_id, self.server.policy.view.scope)
                state = self.server.journal.submit(intent, self.server.policy.check)
                if state.phase == 'recovery_required' and state.run_id is not None and self.server.recover is not None:
                    self.server.recover(intent.key)
                return self._respond(200 if state.terminal else 202, state.receipt().model_dump(mode='json'))
            self._respond(404, {'reason_code': 'launch_route_unknown'})
        except LaunchError as error:
            reason = str(error) if str(error) in ERRORS else 'launch_unavailable'
            self._respond(ERRORS[reason], {'reason_code': reason})
        except Exception:  # Never expose journal paths, peer payloads or credentials.
            self._respond(503, {'reason_code': 'launch_unavailable'})

    def do_GET(self): self._handle(False)
    def do_POST(self): self._handle(True)
