"""Explicit local credential configuration; request fields never grant authority."""

import hmac

from .publication.model import UploadError


class Credentials:
    def __init__(self, entries):
        self._entries = tuple(entries)
        tokens = [token for token, _ in self._entries]
        if not tokens or len(set(tokens)) != len(tokens) or any(len(token) < 32 for token in tokens):
            raise ValueError("Unique configured credentials of at least 32 characters required")

    def authenticate(self, header):
        token = header[7:] if header and header.startswith("Bearer ") else ""
        principal = None
        for expected, candidate in self._entries:
            if hmac.compare_digest(expected.encode(), token.encode()):
                principal = candidate
        if principal is None:
            raise UploadError("unauthenticated")
        return principal
