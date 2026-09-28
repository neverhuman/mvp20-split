"""Bounded authenticated HTTP, without redirects, proxies or implicit retries."""

import math
from dataclasses import dataclass
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class ProtocolError(ValueError):
    """Safe reason only; never embeds credentials, payloads or server diagnostics."""


class TransportLost(ProtocolError):
    """Ambiguous exchange: the request may have committed."""


@dataclass(frozen=True, slots=True)
class Reply:
    status: int
    body: bytes


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpTransport:
    def __init__(self, endpoint: str, token: str, *, timeout: float = 5):
        parsed = urlsplit(endpoint)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or any(c.isspace() for c in endpoint)
            or (parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"})):
            raise ProtocolError("invalid_service_endpoint")
        if not isinstance(token, str) or not 32 <= len(token) <= 512 or not token.isascii() or any(c.isspace() for c in token):
            raise ProtocolError("invalid_service_credential")
        if isinstance(timeout, bool) or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ProtocolError("invalid_transport_timeout")
        self.endpoint = endpoint.rstrip("/")
        self._token = token
        self.timeout = timeout
        self._opener = build_opener(ProxyHandler({}), NoRedirects())

    def request(self, method, path, body=None, *, limit=262144, media_type="application/json"):
        if not path.startswith("/v1/") or any(c in path for c in ("?", "#", "\\", "\r", "\n")):
            raise ProtocolError("invalid_service_path")
        if type(limit) is not int or not 0 <= limit <= 16 * 1024 * 1024:
            raise ProtocolError("invalid_response_limit")
        headers = {"Authorization": "Bearer " + self._token, "Content-Type": media_type}
        request = Request(self.endpoint + path, method=method, data=body, headers=headers)
        try:
            try:
                response = self._opener.open(request, timeout=self.timeout)
            except HTTPError as error:
                response = error
            with response:
                payload = response.read(limit + 1)
                if len(payload) > limit:
                    raise ProtocolError("response_limit_exceeded")
                return Reply(response.status, payload)
        except (URLError, OSError, TimeoutError, HTTPException) as error:
            raise TransportLost("transport_lost") from error
