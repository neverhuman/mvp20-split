"""Explicit scoped grants; tokens are hashed and excluded from diagnostics."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import Scope


class AccessDenied(ValueError):
    pass


@dataclass(frozen=True)
class Principal:
    actor_id: str
    scope: Scope
    actions: frozenset[str]

    def require(self, action: str, scope: Scope):
        if action not in self.actions or scope != self.scope:
            raise AccessDenied("access_denied")


class Credentials:
    def __init__(self, entries: list[tuple[str, Principal]]):
        self._grants = {}
        for token, principal in entries:
            if not isinstance(token, str) or not 32 <= len(token) <= 512 or not token.isascii() or any(ord(char) < 33 or ord(char) > 126 for char in token):
                raise ValueError("Invalid Research credential configuration")
            digest = hashlib.sha256(token.encode()).digest()
            if digest in self._grants:
                raise ValueError("Duplicate Research credential configuration")
            self._grants[digest] = principal

    def authenticate(self, authorization: str | None) -> Principal:
        if authorization is None or not authorization.startswith("Bearer ") or len(authorization) > 519:
            raise AccessDenied("unauthorized")
        try:
            digest = hashlib.sha256(authorization[7:].encode("ascii")).digest()
        except UnicodeEncodeError as error:
            raise AccessDenied("unauthorized") from error
        principal = self._grants.get(digest)
        if principal is None:
            raise AccessDenied("unauthorized")
        return principal
