"""Bounded output members and attempt/report lineage at one checked graph revision."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import (
    GraphAttemptView,
    GraphNodeDetail,
    GraphOutputSummary,
    GraphValueItem,
    GraphValuePage,
)
from pydantic import ValidationError
from sqlalchemy import text

from ..coordinator.values import BoundValues
from ..inspection.cursors import InspectionError
from .policy import ObservedCut, node_view, page_limit, read_transaction, require


@dataclass(frozen=True)
class OutputMembers:
    port: str
    value: object

    @property
    def items(self):
        return self.value.items if self.value.kind == "collection" else (self.value,)

    def summary(self):
        return GraphOutputSummary(port=self.port, kind=self.value.kind, item_count=len(self.items),
            missing_count=sum(item.kind == "missing" for item in self.items),
            artifact=self.value.artifact if self.value.kind == "artifact" else None)

    def page(self, after, limit):
        return tuple(GraphValueItem(index=index, value=self.items[index]) for index in
            range(after + 1, min(len(self.items), after + limit + 1)))


@dataclass(frozen=True)
class ObservedNode:
    row: object
    exports: tuple

    @classmethod
    def load(cls, conn, cut, activation_id):
        row = conn.execute(text("SELECT n.*,s.parent_activation_id FROM runtime.graph_nodes n "
            "JOIN runtime.graph_scopes s USING (tenant_id,project_id,run_id,scope_key) WHERE "
            "n.tenant_id=:tenant AND n.project_id=:project AND n.run_id=:run AND n.activation_id=:activation"),
            {**cut.params, "activation": activation_id}).mappings().one_or_none()
        require(row is not None, "graph_node_unavailable")
        try:
            values = BoundValues.from_records(row["outputs"] or []).bindings
        except (ValidationError, ValueError, TypeError) as error:
            raise InspectionError("snapshot_unavailable") from error
        return cls(row, tuple(OutputMembers(binding.port, binding.value) for binding in values))

    def output(self, port):
        value = next((value for value in self.exports if value.port == port), None)
        require(value is not None, "graph_output_unavailable")
        return value


class GraphDetails:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    def node(self, principal, run_id, activation_id, *, snapshot_token, cursor=None, limit=50):
        page_limit(limit)
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            snapshot = cut.snapshot_position(self.cursors, snapshot_token)
            observed = ObservedNode.load(conn, cut, activation_id)
            mode = "graph-attempts:" + activation_id
            position = cut.position(self.cursors, cursor, mode) if cursor else snapshot
            params = {**cut.params, "activation": activation_id, "fence": position.after[0], "after": position.after[2], "limit": limit + 1}
            rows = conn.execute(text("SELECT a.attempt_id,v.invocation_id,a.worker_id,a.fence,a.status,a.settled,"
                "r.report_id AS completion_id,EXISTS(SELECT 1 FROM runtime.accepted_completions c "
                "WHERE (c.tenant_id,c.project_id,c.run_id,c.attempt_id)=(a.tenant_id,a.project_id,a.run_id,a.attempt_id)) AS canonical_result "
                "FROM runtime.attempts a JOIN runtime.activations v USING (tenant_id,project_id,run_id,activation_id) "
                "LEFT JOIN runtime.attempt_reports r USING (tenant_id,project_id,run_id,activation_id,attempt_id) "
                "WHERE a.tenant_id=:tenant AND a.project_id=:project AND a.run_id=:run AND a.activation_id=:activation "
                "AND (a.fence,a.attempt_id)>(:fence,:after) ORDER BY a.fence,a.attempt_id LIMIT :limit"), params).mappings().all()
            visible = rows[:limit]
            following = None
            if len(rows) > limit:
                from dataclasses import replace
                following = self.cursors.encode(replace(position, mode=mode,
                    after=(visible[-1]["fence"], 0, visible[-1]["attempt_id"])))
            return GraphNodeDetail(cut=cut.to_wire(), node=node_view(observed.row), scope_key=observed.row["scope_key"],
                parent_activation_id=observed.row["parent_activation_id"], outputs=tuple(value.summary() for value in observed.exports),
                attempts=tuple(GraphAttemptView.model_validate(dict(row)) for row in visible), next_cursor=following)

    def values(self, principal, run_id, activation_id, port, *, snapshot_token, cursor=None, limit=50):
        page_limit(limit)
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            snapshot = cut.snapshot_position(self.cursors, snapshot_token)
            members = ObservedNode.load(conn, cut, activation_id).output(port)
            mode = "graph-values:" + activation_id + ":" + port
            position = cut.position(self.cursors, cursor, mode) if cursor else snapshot
            after = position.after[0]
            require(-1 <= after < max(1, len(members.items)), "invalid_cursor")
            items = members.page(after, limit)
            following = None
            if items and items[-1].index + 1 < len(members.items):
                from dataclasses import replace
                following = self.cursors.encode(replace(position, mode=mode, after=(items[-1].index, 0, "")))
            return GraphValuePage(cut=cut.to_wire(), activation_id=activation_id, port=port,
                item_count=len(members.items), items=items, next_cursor=following)
