"""Passive Await transitions under the Graph Runner's existing run lock and audit."""

from sqlalchemy import text

from ..compiler.catalog import canonical
from ..lifecycle.claims import RUN
from .closures import WaitClosures, load_wait
from .disposition import WaitDisposition
from .intents import WaitIntents
from .model import WaitAddress, WaitRecord, ensure
from .storage import WaitRecords


def stop_waits(conn, params, run, leases, reason):
    rows = conn.execute(text("SELECT w.activation_id FROM runtime.graph_waits w WHERE w.tenant_id=:tenant "
        "AND w.project_id=:project AND w.run_id=:run AND NOT EXISTS (SELECT 1 FROM runtime.graph_wait_closures c "
        "WHERE (c.tenant_id,c.project_id,c.run_id,c.activation_id)=(w.tenant_id,w.project_id,w.run_id,w.activation_id)) "
        "ORDER BY w.activation_id"), params).scalars().all()
    for activation in rows:
        wait = load_wait(conn, {**params, "activation": activation})
        WaitClosures.persist(conn, WaitDisposition(wait, "cancelled", reason), run["revision"] + 1)
    return WaitIntents(leases).abort(conn, params, reason)


class WaitExecution:
    def __init__(self, conn, params, plan, graph, run, leases):
        self.conn, self.params, self.plan, self.graph, self.run = conn, params, plan, graph, run
        self.intents = WaitIntents(leases)
        self.terminal_intents = []

    def step(self, scope, row, node):
        now = self.conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        params = {**self.params, "activation": row["activation_id"]}
        if row["status"] == "ready":
            value = scope.environment.source(node.subject)
            ensure(value.kind == "artifact", "wait_artifact_subject_required")
            address = WaitAddress(self.plan.document.definition.scope, self.params["run"], row["activation_id"], self.plan.sha256)
            record = WaitRecord.pin(address, node, value.artifact, opened_at=now, run_deadline=self.graph["deadline"])
            WaitRecords.open(self.conn, record, self.run["revision"] + 1)
            state = {**row["state"], "expectation_sha256": record.sha256, "wait_revision": record.expectation.wait_revision}
            self.conn.execute(text("UPDATE runtime.graph_nodes SET status='issued',state=CAST(:state AS jsonb) WHERE " +
                RUN + " AND activation_id=:activation"), {**params, "state": canonical(state).decode()})
            return True
        wait = load_wait(self.conn, params)
        if now < wait.deadline:
            return False
        WaitClosures.persist(self.conn, WaitDisposition.timeout(wait, now), self.run["revision"] + 1)
        self.terminal_intents.extend(self.intents.abort(self.conn, self.params, "wait_deadline_expired",
                                                       activation=row["activation_id"]))
        return True
