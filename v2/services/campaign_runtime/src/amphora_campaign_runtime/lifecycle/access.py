"""Configured local runtime principals; no caller-authored grants."""

import hmac
from dataclasses import dataclass

from amphora_contracts_core import Scope

from .model import TransitionError


@dataclass(frozen=True, slots=True)
class RuntimePrincipal:
    actor_id: str
    scope: Scope
    actions: frozenset[str]

    def require(self, action, identity):
        if action not in self.actions or identity.actor_id != self.actor_id or identity.scope != self.scope:
            raise TransitionError("access_denied")


class RuntimeCredentials:
    def __init__(self, entries):
        self.entries = tuple(entries)
        if (not self.entries or any(len(token) < 32 for token, _ in self.entries)
            or len({token for token, _ in self.entries}) != len(self.entries)):
            raise ValueError("Unique configured credentials of at least 32 characters required")

    def authenticate(self, authorization):
        if authorization and authorization.startswith("Bearer "):
            supplied = authorization[7:].encode()
            for token, principal in self.entries:
                if hmac.compare_digest(supplied, token.encode()):
                    return principal
        raise TransitionError("unauthenticated")
