"""Scoped read cuts and signed positions shared by bounded observation projections."""

import json
from contextlib import contextmanager
from dataclasses import dataclass, replace

from amphora_contracts_graph_runtime import GraphNodeViewV3, GraphReadBudget, GraphReadCut
from sqlalchemy import text

from ..inspection.cursors import InspectionError


def require(condition, reason="snapshot_unavailable"):
    if not condition:
        raise InspectionError(reason)


def page_limit(limit):
    require(type(limit) is int and 1 <= limit <= 100, "invalid_page_request")


@contextmanager
def read_transaction(engine):
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
        conn.execute(text("SET TRANSACTION READ ONLY"))
        yield conn


@dataclass(frozen=True)
class ObservedCut:
    scope: object
    row: object

    @classmethod
    def load(cls, conn, principal, run_id):
        principal.require("read")
        row = conn.execute(text("SELECT r.run_id,r.revision,r.status,r.budget_limit,r.reserved,r.spent,"
            "g.plan_sha256,g.frontier_revision FROM runtime.runs r JOIN runtime.graph_runs g "
            "USING (tenant_id,project_id,run_id) WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run"),
            {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id, "run": run_id}).mappings().one_or_none()
        require(row is not None, "run_unavailable")
        return cls(principal.scope, row)

    @property
    def params(self):
        return {"tenant": self.scope.tenant_id, "project": self.scope.project_id, "run": self.row["run_id"]}

    @property
    def revision(self):
        return self.row["revision"]

    def to_wire(self):
        return GraphReadCut(scope=self.scope, **{key: self.row[key] for key in
            ("run_id", "plan_sha256", "revision", "frontier_revision")})

    def budget(self):
        return GraphReadBudget(limit=self.row["budget_limit"], reserved=self.row["reserved"], spent=self.row["spent"])

    def position(self, cursors, token, mode, *, resource=None, filter=None, after=(-1, -1, "")):
        resource = resource or self.row["run_id"]
        position = cursors.decode(token, mode=mode, scope=self.scope, resource=resource, filter=filter) if token else cursors.start(
            mode, self.scope, resource, self.revision, after, filter)
        require(position.revision == self.revision)
        return position

    def snapshot_position(self, cursors, token):
        require(isinstance(token, str) and bool(token), "invalid_page_request")
        return self.position(cursors, token, "graph-snapshot")

    def tokens(self, cursors, position):
        snapshot = replace(position, mode="graph-snapshot", filter=None, after=(-1, -1, ""))
        events = replace(snapshot, mode="graph-events", after=(self.revision, 0, ""))
        return cursors.encode(snapshot), cursors.encode(events)


def node_view(row):
    return GraphNodeViewV3.model_validate_json(json.dumps({key: row[key] for key in
        ("activation_id", "path", "kind", "status", "reason_code")}))
