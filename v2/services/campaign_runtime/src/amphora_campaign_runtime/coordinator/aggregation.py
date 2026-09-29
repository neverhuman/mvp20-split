"""Map accepted owner observations to one atomic, immutable collection decision."""

from amphora_contracts_graph_runtime import GraphBinding
from sqlalchemy import text

from ..aggregation import (
    AggregateCuts,
    AggregateIdentity,
    CollectionWindow,
    JoinAccumulator,
    MemberSnapshot,
    SnapshotCut,
)
from ..lifecycle.claims import RUN
from .state import persist_node
from .values import BoundValues


class GraphAggregation:
    def __init__(self, conn, params, plan, graph):
        self.conn, self.params, self.plan, self.graph = conn, params, plan, graph
        self.revision = conn.execute(text("SELECT revision FROM runtime.runs WHERE " + RUN), params).scalar_one()

    def expired(self, scope, node):
        now = self.conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        return CollectionWindow(scope.record["opened_at"], self.graph["deadline"]).expired(node.policy, now)

    def member(self, key, status, required, value, reason=None):
        if status in {"waiting", "ready", "issued", "active"}:
            status = "pending"
        if status == "failed" and reason in {"tool_abstained", "tool_cancelled"}:
            status = reason.removeprefix("tool_")
        return MemberSnapshot(key, required, status, self.revision, value,
                              None if status == "succeeded" else reason or "member_" + status)

    def close(self, row, node, members, trigger="all_terminal"):
        identity = AggregateIdentity(self.plan.document.definition.scope, self.params["run"], row["activation_id"])
        cut = SnapshotCut(identity, self.revision, self.revision + 1, trigger, tuple(members))
        decision = JoinAccumulator(node.policy).close(cut)
        outputs = None
        if decision.collection is not None:
            outputs = BoundValues((GraphBinding(port=node.output.name, value=decision.collection),))
            outputs.validate((node.output,), self.plan.document.definition.scope)
        digest = AggregateCuts.decide(self.conn, decision)
        persist_node(self.conn, self.params, row, decision.status, outputs=outputs,
                     reason=decision.reason_code, state={**row["state"], "aggregate_decision_sha256": digest})
        return True

    def join(self, scope, row, node):
        members = []
        for member in node.members:
            source = scope.nodes[member.source.node_id] if member.source.kind == "output" else None
            status = source["status"] if source is not None else "succeeded"
            value = scope.environment.source(member.source) if status == "succeeded" else None
            reason = source["reason_code"] if source is not None else None
            outcome = source["state"].get("tool_outcome") if source is not None else None
            if source is not None and source["kind"] == "await":
                outcome = source["state"].get("wait_outcome")
            if status == "failed" and outcome is not None:
                status, reason = outcome["status"], outcome["reason_code"]
            members.append(self.member(member.member_id, status, member.required, value,
                                       reason))
        trigger = "deadline" if any(member.status == "pending" for member in members) else "all_terminal"
        return self.close(row, node, members, trigger)
