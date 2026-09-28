"""Owner-local settlement under run locks; no inferred refund of issued work."""

import uuid
from dataclasses import dataclass

from sqlalchemy import text

from .claims import RUN, RuntimeLeases, lease_from
from .model import ActivationState, RunBudget, RunState, TransitionError


@dataclass(frozen=True, slots=True)
class SettlementDecision:
    status: str
    budget: RunBudget
    expired: tuple
    cancelled: tuple
    changed: bool


class BudgetSettlement:
    def __init__(self, engine):
        self.leases = RuntimeLeases(engine)

    def sweep(self, principal, run_id):
        principal.require("maintain")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id, "run": run_id}
        def transaction(conn):
            run = self.leases._run(conn, params)
            decision = self.apply(conn, params, run, stop=run["status"] == "cancelled")
            if decision.changed:
                self.leases._changed(conn, params, run, decision.budget, uuid.uuid4().hex,
                    {"kind": "budget_settled", "expired": decision.expired, "cancelled": decision.cancelled,
                     "status": decision.status})
                conn.execute(text("UPDATE runtime.runs SET status=:status WHERE " + RUN),
                             {**params, "status": decision.status})
            return decision
        return self.leases.commands.transact(transaction)

    def apply(self, conn, params, run, *, stop=False):
        """Caller holds run lock and owns the final budget/revision/audit transaction."""
        if not conn.in_transaction():
            raise ValueError("Owner transaction required")
        budget = RunBudget(run["budget_limit"], run["reserved"], run["spent"])
        state = RunState("cancelled" if stop else run["status"], run["revision"])
        max_attempts = run["input_snapshot"]["budget"]["max_attempts_per_activation"]
        rows = conn.execute(text("SELECT * FROM runtime.activations WHERE " + RUN +
                                  " ORDER BY activation_id FOR UPDATE"), params).mappings().all()
        now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        expired, cancelled, projections = [], [], []
        changed = False
        for row in rows:
            status = row["status"]
            if status == "leased":
                attempt = conn.execute(text("SELECT * FROM runtime.attempts WHERE " + RUN +
                    " AND activation_id=:activation AND fence=:fence FOR UPDATE"),
                    {**params, "activation": row["activation_id"], "fence": row["current_fence"]}).mappings().one()
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                if stop or now >= attempt["lease_expires_at"]:
                    activation = ActivationState(status, row["current_fence"], row["attempt_count"], max_attempts,
                                                 row["specification"].get("side_effects", "pure"))
                    disposition = "cancelled" if stop and activation.effect == "pure" else "uncertain" if stop else "expired"
                    activation, lease, budget = activation.terminal(lease_from(attempt), budget, disposition,
                                                                    now=now, run=state)
                    conn.execute(text("UPDATE runtime.attempts SET status=:status,settled=:settled WHERE " + RUN +
                        " AND attempt_id=:attempt"), {**params, "attempt": lease.attempt_id,
                            "status": lease.status, "settled": lease.settled})
                    status = activation.status
                    (cancelled if stop else expired).append(lease.attempt_id)
            projections.append((row, status))
        final = []
        for row, status in projections:
            if status == "queued":
                if stop:
                    status = "cancelled"
                elif (row["deadline"] is not None and now >= row["deadline"]) or (budget.available == 0 and budget.reserved == 0):
                    status = "failed"
            if status != row["status"]:
                conn.execute(text("UPDATE runtime.activations SET status=:status WHERE " + RUN +
                    " AND activation_id=:activation"), {**params, "activation": row["activation_id"], "status": status})
                changed = True
            final.append(status)
        changed = changed or bool(expired or cancelled)
        if (changed or stop) and conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.completion_intents WHERE " + RUN +
                                          " AND status='prepared')"), params).scalar_one():
            raise TransitionError("prepared_intent_requires_reconciliation")
        status = run["status"]
        if "uncertain" in final:
            status = "blocked"
        elif stop:
            status = "cancelled"
        elif final and all(s in {"succeeded", "abstained", "failed", "cancelled"} for s in final) and "failed" in final:
            status = "failed"
        # Completion success is owned by the completion service, not inferred by this maintenance pass.
        return SettlementDecision(status, budget, tuple(expired), tuple(cancelled), changed or status != run["status"])
