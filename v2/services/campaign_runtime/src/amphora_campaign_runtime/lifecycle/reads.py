"""Scoped, consistent owner projections; snapshots carry no execution authority."""

from dataclasses import dataclass
from datetime import UTC

from amphora_contracts_runtime import RunSnapshot
from sqlalchemy import text

from .claims import RUN
from .model import RunBudget, TransitionError


def wire_time(value):
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ObservedRun:
    scope: object
    run: object
    activations: tuple

    def to_response(self):
        run = self.run
        budget = RunBudget(run["budget_limit"], run["reserved"], run["spent"])
        activations = []
        for row in self.activations:
            attempt = None if row["attempt_id"] is None else {
                "attempt_id": row["attempt_id"], "worker_id": row["worker_id"], "fence": row["current_fence"],
                "status": row["attempt_status"], "lease_expires_at": wire_time(row["lease_expires_at"]),
                "deadline": wire_time(row["deadline"])}
            activations.append({"activation_id": row["activation_id"], "invocation_id": row["invocation_id"],
                "status": row["status"], "fence": row["current_fence"], "attempt_count": row["attempt_count"],
                "latest_attempt": attempt})
        return RunSnapshot.model_validate({"scope": self.scope, "run_id": run["run_id"],
            "fixture_id": run["fixture_id"], "plan_sha256": run["plan_sha256"], "status": run["status"],
            "revision": run["revision"], "budget": {"limit": budget.limit, "reserved": budget.reserved,
            "spent": budget.spent, "available": budget.available}, "activations": tuple(activations)})


class RuntimeReads:
    def __init__(self, engine):
        self.engine = engine

    def run(self, principal, run_id):
        principal.require("read")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id, "run": run_id}
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            run = conn.execute(text("SELECT * FROM runtime.runs WHERE " + RUN), params).mappings().one_or_none()
            if run is None:
                raise TransitionError("run_unavailable")
            active = "AND v.status IN ('queued','leased') " if run["execution_mode"] == "graph" else ""
            rows = conn.execute(text("SELECT v.activation_id,v.invocation_id,v.status,v.current_fence,v.attempt_count,"
                "a.attempt_id,a.worker_id,a.status AS attempt_status,a.lease_expires_at,a.deadline "
                "FROM runtime.activations v LEFT JOIN runtime.attempts a ON "
                "(a.tenant_id,a.project_id,a.run_id,a.activation_id,a.fence)="
                "(v.tenant_id,v.project_id,v.run_id,v.activation_id,v.current_fence) "
                "WHERE v.tenant_id=:tenant AND v.project_id=:project AND v.run_id=:run "
                + active + "ORDER BY v.activation_id LIMIT 256"), params).mappings().all()
            return ObservedRun(principal.scope, run, tuple(rows)).to_response()
