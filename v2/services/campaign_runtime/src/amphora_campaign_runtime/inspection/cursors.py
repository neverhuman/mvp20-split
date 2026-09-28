"""Signed, expiring scope/resource/filter-bound inspection cursors."""

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, replace


class InspectionError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class PagePosition:
    mode: str
    scope: dict
    resource: str
    revision: int
    after: tuple
    filter: str | None
    expires: int

    def advance(self, after):
        return replace(self, after=after)


class CursorCodec:
    def __init__(self, key, *, ttl_seconds=900, clock=time.time):
        if len(key.encode()) < 32 or type(ttl_seconds) is not int or not 60 <= ttl_seconds <= 3600:
            raise ValueError("Explicit cursor key and bounded lifetime required")
        self.key, self.ttl, self.clock = key.encode(), ttl_seconds, clock

    def start(self, mode, scope, resource, revision, after, filter=None):
        return PagePosition(mode, scope.model_dump(), resource, revision, after, filter, int(self.clock()) + self.ttl)

    def encode(self, position):
        body = json.dumps({"v": 1, "mode": position.mode, "scope": position.scope, "resource": position.resource,
            "revision": position.revision, "after": position.after, "filter": position.filter,
            "expires": position.expires}, sort_keys=True, separators=(",", ":")).encode()
        encoded = base64.urlsafe_b64encode(body).rstrip(b"=").decode()
        return encoded + "." + hmac.new(self.key, encoded.encode(), hashlib.sha256).hexdigest()

    def decode(self, value, *, mode, scope, resource, filter=None):
        try:
            if len(value) > 4096:
                raise ValueError
            encoded, supplied = value.split(".")
            signature = hmac.new(self.key, encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(supplied, signature):
                raise ValueError
            raw = base64.b64decode(encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
            body = json.loads(raw)
            if set(body) != {"v", "mode", "scope", "resource", "revision", "after", "filter", "expires"} or body["v"] != 1:
                raise ValueError
            if (type(body["revision"]) is not int or body["revision"] < 0 or type(body["expires"]) is not int
                or len(body["after"]) != 3 or any(type(v) is not int for v in body["after"][:2])
                or not isinstance(body["after"][2], str)):
                raise ValueError
            position = PagePosition(body["mode"], body["scope"], body["resource"], body["revision"],
                                    tuple(body["after"]), body["filter"], body["expires"])
        except (ValueError, TypeError, KeyError, UnicodeError) as error:
            raise InspectionError("invalid_cursor") from error
        if position.expires <= self.clock():
            raise InspectionError("cursor_expired")
        if (position.mode, position.scope, position.resource, position.filter) != (mode, scope.model_dump(), resource, filter):
            raise InspectionError("cursor_mismatch")
        return position
