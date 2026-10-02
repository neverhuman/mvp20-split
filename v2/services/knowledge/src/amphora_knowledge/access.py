"""Trusted adapter supplies scoped principals; graph payloads cannot supply grants."""

import re
from dataclasses import dataclass

from amphora_contracts_core import Scope

from .authoring.canonical import KnowledgeError


@dataclass(frozen=True)
class Principal:
    actor_id: str
    scope: Scope
    actions: frozenset[str]

    def __post_init__(self):
        if not isinstance(self.actor_id, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", self.actor_id) is None:
            raise KnowledgeError("invalid_principal")

    def require(self, action, scope):
        if action not in self.actions or scope != self.scope:
            raise KnowledgeError("access_denied")
