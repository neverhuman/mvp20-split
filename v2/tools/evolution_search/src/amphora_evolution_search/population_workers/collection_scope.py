"""Current collector occurrence affinity; candidate identity still comes from inputs."""
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphNodeViewV3

from ..ranking import require
from .method_plan import PrimaryMethodPlan, authored_invocation


@dataclass(frozen=True)
class CollectionScope:
    plan: PrimaryMethodPlan
    caller: GraphNodeViewV3

    @classmethod
    def load(cls, capture, plan, invocation):
        require(capture.snapshot.cut.plan_sha256 == plan.execution.sha256, "population_collection_scope_plan")
        own = tuple(node for node in capture.nodes if node.activation_id == invocation.activation_id)
        require(len(own) == 1 and own[0].kind == "invoke" and own[0].status == "issued"
                and own[0].path.node_id == invocation.node_id, "population_collection_scope_caller")
        caller = own[0]
        require(authored_invocation(plan.execution, caller).tool == invocation.tool,
                "population_collection_scope_tool")
        prefix = tuple(frame.node_id for frame in caller.path.occurrences)
        require(plan.scope_path[:len(prefix)] == prefix, "population_collection_scope_path")
        return cls(plan, caller)

    def binding(self, node):
        prefix = self.caller.path.occurrences
        if node.path.occurrences[:len(prefix)] != prefix:
            return None
        return self.plan.binding(node)
