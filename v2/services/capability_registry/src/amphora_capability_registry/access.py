"""Configured credentials map to principals, never payload-provided grants."""

import hmac

from .catalog.model import RegistryDenied


class Credentials:
    def __init__(self, entries):
        self.entries = tuple(entries)
        tokens = [token for token, _ in self.entries]
        if any(not isinstance(token, str) or not token.isascii() or not 32 <= len(token) <= 512 for token in tokens) or len(tokens) != len(set(tokens)):
            raise ValueError("Unique bounded opaque tokens required")

    def authenticate(self, header):
        if not header or not header.startswith("Bearer "):
            raise RegistryDenied("authentication_required")
        token = header[7:]
        if not token.isascii() or len(token) > 512:
            raise RegistryDenied("authentication_required")
        for expected, principal in self.entries:
            if hmac.compare_digest(token, expected):
                return principal
        raise RegistryDenied("authentication_required")
