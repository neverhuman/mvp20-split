"""Reviewed exact compiled plans and immutable public tool metadata; no discovery I/O."""

from dataclasses import dataclass
from types import MappingProxyType

from ..compiler import compile_campaign
from ..lifecycle.model import TransitionError
from .values import ensure


@dataclass(frozen=True)
class ReviewedPlan:
    plan: object
    descriptors: tuple

    @classmethod
    def compile(cls, definition, tools, schemas):
        plan = compile_campaign(definition, tools, schemas)
        descriptors = tuple(tools.require(lock.tool, "admission").descriptor.tool for lock in plan.document.lock.tools)
        return cls(plan, descriptors)

    @property
    def scope(self):
        return self.plan.document.definition.scope

    def descriptor(self, tool):
        for descriptor in self.descriptors:
            if descriptor.binding == tool:
                return descriptor
        raise TransitionError("graph_tool_pin_unavailable")


class PlanCatalog:
    def __init__(self, entries):
        entries = tuple(entries)
        keyed = {(entry.scope.tenant_id, entry.scope.project_id, entry.plan.sha256): entry for entry in entries}
        ensure(len(keyed) == len(entries), "duplicate_reviewed_plan")
        self._entries = MappingProxyType(keyed)

    def require(self, scope, digest):
        entry = self._entries.get((scope.tenant_id, scope.project_id, digest))
        ensure(entry is not None, "graph_plan_unavailable")
        return entry
