"""Trusted adapter principal, never model text or a caller-selected wire permission."""

from dataclasses import dataclass

from amphora_contracts_core import Identifier, Scope
from pydantic import TypeAdapter


@dataclass(frozen=True)
class Principal:
    actor_id: str
    scope: Scope
    actions: frozenset[str]

    def __post_init__(self):
        TypeAdapter(Identifier).validate_python(self.actor_id, strict=True)
        object.__setattr__(self, "scope", Scope.model_validate_json(self.scope.model_dump_json(warnings=False)))
        actions = frozenset(self.actions)
        if not actions <= {"record_requests", "record_attempts", "read_attempts", "propose_topology", "read_topology"}:
            raise ValueError("unknown_planning_grant")
        object.__setattr__(self, "actions", actions)

    def require(self, action, scope):
        if scope != self.scope or action not in self.actions:
            raise PermissionError("planning_access_denied")
