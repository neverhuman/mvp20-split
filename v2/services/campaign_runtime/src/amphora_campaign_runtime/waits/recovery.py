"""Reconcile waits left behind when another owner transition terminated the graph."""

import uuid

from sqlalchemy import text

from ..completion.retention import queue_terminal
from ..lifecycle.claims import RuntimeLeases
from ..lifecycle.model import RunBudget
from .execution import stop_waits

OPEN_WAITS = ("SELECT 1 FROM runtime.graph_waits w WHERE (w.tenant_id,w.project_id,w.run_id)="
    "(r.tenant_id,r.project_id,r.run_id) AND NOT EXISTS (SELECT 1 FROM runtime.graph_wait_closures c WHERE "
    "(c.tenant_id,c.project_id,c.run_id,c.activation_id)=(w.tenant_id,w.project_id,w.run_id,w.activation_id))")


class WaitRecovery:
    def __init__(self, engine):
        self.engine, self.leases = engine, RuntimeLeases(engine)

    def tick(self, principal):
        """At most one terminal run per scoped polling tick; never reopens it."""
        principal.require("maintain")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id}
        with self.engine.connect() as conn:
            key = conn.execute(text("SELECT r.run_id FROM runtime.runs r WHERE r.tenant_id=:tenant "
                "AND r.project_id=:project AND r.execution_mode='graph' AND r.status<>'running' AND (EXISTS (" +
                OPEN_WAITS + ") OR EXISTS (SELECT 1 FROM runtime.wait_retention_intents i WHERE "
                "(i.tenant_id,i.project_id,i.run_id)=(r.tenant_id,r.project_id,r.run_id) AND i.status='prepared')) "
                "ORDER BY r.run_id LIMIT 1"), params).scalar_one_or_none()
        if key is None:
            return False
        params["run"] = key

        def transaction(conn):
            run = self.leases._run(conn, params)
            open_waits = conn.execute(text("SELECT EXISTS (" + OPEN_WAITS + ") FROM runtime.runs r WHERE " +
                "r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run"),
                params).scalar_one()
            aborted = stop_waits(conn, params, run, self.leases, "run_not_running")
            if not open_waits and not aborted:
                return False
            self.leases._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
                uuid.uuid4().hex, {"kind": "terminal_waits_reconciled", "aborted_intents": aborted,
                                  "status": run["status"]})
            queue_terminal(conn, params, aborted)
            return True
        return self.leases.commands.transact(transaction)
