"""Stable conversion address, committed input cut and bounded resource accounting."""

import hashlib
import uuid
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphBinding

from ..compiler.catalog import canonical
from ..coordinator.values import BoundValues, ensure


@dataclass(frozen=True)
class BindingAddress:
    scope: object
    run_id: str
    activation_id: str
    plan_sha256: str

    @property
    def identity(self):
        raw = canonical({"profile": "amphora-binding-address-v1", "scope": self.scope.model_dump(mode="json"),
            "run_id": self.run_id, "activation_id": self.activation_id, "plan_sha256": self.plan_sha256})
        return "binding:" + uuid.uuid5(uuid.NAMESPACE_URL, raw.decode()).hex

    def operation(self, family, slot):
        return uuid.uuid5(uuid.NAMESPACE_URL, canonical([self.identity, family, slot]).decode()).hex


@dataclass(frozen=True)
class BindingInput:
    node: object
    values: BoundValues

    @classmethod
    def resolve(cls, node, environment):
        fields = (("source", node.source),) if node.kind == "artifact_project" else tuple(
            (field.name, field.source) for field in node.fields)
        return cls(node, BoundValues(tuple(GraphBinding(port=name, value=environment.source(source))
                                          for name, source in fields)))

    @property
    def sha256(self):
        node = self.node.model_dump(mode="json")
        if "fields" in node:
            node["fields"].sort(key=lambda field: field["name"])
        return hashlib.sha256(canonical({"profile": "amphora-binding-input-v1", "node": node,
            "inputs": self.values.record()})).hexdigest()


@dataclass
class BindingBudget:
    limits: object
    items: int = 0
    artifacts: int = 0
    bytes: int = 0

    def add(self, *, items=0, artifacts=0, size=0):
        self.items += items
        self.artifacts += artifacts
        self.bytes += size
        ensure(self.items <= self.limits.max_items, "binding_member_budget")
        ensure(self.artifacts <= self.limits.max_artifacts, "binding_artifact_budget")
        ensure(self.bytes <= self.limits.max_bytes, "binding_byte_budget")

    def record(self):
        return {"items": self.items, "artifacts": self.artifacts, "bytes": self.bytes}
