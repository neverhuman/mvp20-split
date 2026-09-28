"""Plan-bound activation identities; occurrence indices are not attempt/fence authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_campaigns import ActivationPath

from .catalog import canonical
from .errors import require


@dataclass(frozen=True)
class ActivationAddress:
    plan_sha256: str
    path: ActivationPath

    @classmethod
    def for_plan(cls, plan, path):
        body = plan.document.definition.body
        for occurrence in path.occurrences:
            nodes = {node.node_id: node for node in body.nodes}
            require(occurrence.node_id in nodes, "unknown_occurrence_node", "activation")
            node = nodes[occurrence.node_id]
            expected = "iterate" if occurrence.kind == "loop" else "scatter"
            require(node.kind == expected, "occurrence_kind_mismatch", "activation")
            maximum = node.max_iterations if node.kind == "iterate" else node.max_members
            require(occurrence.index < maximum, "occurrence_bound", "activation")
            body = node.body
        require(path.node_id in {node.node_id for node in body.nodes}, "unknown_activation_node", "activation")
        return cls(plan.sha256, path)

    @property
    def key(self):
        return hashlib.sha256(canonical({"profile": "amphora-activation-address-v1", "plan_sha256": self.plan_sha256,
                                         "path": self.path.model_dump(mode="json")})).hexdigest()
