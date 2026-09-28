"""Pure immutable scope/node scheduling intents; storage and attempt authority are separate."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaigns import ActivationPath

from ..compiler import ActivationAddress
from ..compiler.catalog import canonical
from .values import ensure


@dataclass(frozen=True)
class ScopeAddress:
    plan_sha256: str
    occurrences: tuple = ()

    @property
    def key(self):
        return hashlib.sha256(canonical({"profile": "amphora-graph-scope-v1", "plan_sha256": self.plan_sha256,
                                        "occurrences": [value.model_dump(mode="json") for value in self.occurrences]})).hexdigest()

    @property
    def definition_path(self):
        return tuple(value.node_id for value in self.occurrences)


@dataclass(frozen=True)
class NodeIntent:
    address: ActivationAddress
    scope_key: str
    kind: str
    priority: tuple
    status: str


class FrontierPlanner:
    def scope(self, plan, address):
        """Declare every node once; only nodes without incoming controls start ready."""
        ensure(plan.sha256 == address.plan_sha256, "graph_scope_plan_mismatch")
        body = plan.document.definition.body
        priority = []
        compiled_scopes = {scope.path: scope for scope in plan.document.scopes}
        for depth, occurrence in enumerate(address.occurrences):
            parent = compiled_scopes[address.definition_path[:depth]]
            priority.extend((parent.order.index(occurrence.node_id), occurrence.index))
            body = next(node.body for node in body.nodes if node.node_id == occurrence.node_id)
        compiled = compiled_scopes[address.definition_path]
        blocked = {edge.target for edge in body.edges}
        nodes = {node.node_id: node for node in body.nodes}
        intents = []
        for index, key in enumerate(compiled.order):
            path = ActivationPath.model_validate_json(json.dumps({"schema_version": "2", "node_id": key,
                "occurrences": [value.model_dump(mode="json") for value in address.occurrences]}))
            activation = ActivationAddress.for_plan(plan, path)
            intents.append(NodeIntent(activation, address.key, nodes[key].kind, (*priority, index),
                                      "waiting" if key in blocked else "ready"))
        return tuple(intents)
