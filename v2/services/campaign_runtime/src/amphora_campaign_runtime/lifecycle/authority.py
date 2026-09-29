"""Atomic owner cancellation and revocation; configured grants precede live state checks."""

import json
import uuid

from amphora_contracts_runtime import CancelRun, RevokeWorker
from sqlalchemy import text

from ..artifact_bindings.storage import stop_bindings
from ..completion.retention import queue_terminal
from ..persistence.commands import _bindings
from ..waits.execution import stop_waits
from .claims import RUN, SCOPE, RuntimeLeases, lease_from
from .intents import AbortDecision
from .model import ActivationState, RunBudget, RunState, TransitionError
from .receipts import RuntimeReply
from .settlement import BudgetSettlement


def lock_work(conn, params):
    conn.execute(text("SELECT activation_id FROM runtime.activations WHERE " + RUN +
                      " ORDER BY activation_id FOR UPDATE"), params).all()
    conn.execute(text("SELECT attempt_id FROM runtime.attempts WHERE " + RUN +
                      " ORDER BY activation_id,fence FOR UPDATE"), params).all()


class AuthorityCommands:
    def __init__(self, engine):
        self.leases = RuntimeLeases(engine)
        self.settlement = BudgetSettlement(engine)
        self.commands = self.leases.commands

    def cancel(self, principal, command):
        principal.require("cancel", command.identity)
        if command.identity.command_family != "runtime.cancel":
            raise TransitionError("wrong_command_family")
        request = CancelRun.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.commands.register(command)
        reply = RuntimeReply(command, registered.operation_id)
        params = {**_bindings(command), "run": request.run_id}

        def transaction(conn):
            try:
                run = self.leases._run(conn, params)
                existing = self.leases._existing(conn, command)
                if existing is not None:
                    return existing
                RunState(run["status"], run["revision"]).cancel(request.expected_run_revision)
            except TransitionError as error:
                return self.leases._finish(conn, command, reply.reject(str(error)))
            if run["status"] == "cancelled":
                return self.leases._finish(conn, command, reply.accepted("run", request.run_id, run["revision"]))
            lock_work(conn, params)
            aborted = AbortDecision(registered.operation_id, request.reason_code).apply(conn, params)
            if run["execution_mode"] == "graph":
                aborted += stop_waits(conn, params, run, self.leases, request.reason_code)
                aborted += stop_bindings(conn, params, run, request.reason_code)
            decision = self.settlement.apply(conn, params, run, stop=True)
            revision = self.leases._changed(conn, params, run, decision.budget, registered.operation_id,
                {"kind": "run_cancelled", "reason_code": request.reason_code, "aborted_intents": aborted,
                 "status": decision.status})
            conn.execute(text("UPDATE runtime.runs SET status=:status WHERE " + RUN),
                         {**params, "status": decision.status})
            queue_terminal(conn, params, aborted)
            return self.leases._finish(conn, command, reply.accepted("run", request.run_id, revision))
        return self.commands.transact(transaction)

    def revoke(self, principal, command):
        principal.require("revoke", command.identity)
        if command.identity.command_family != "runtime.revoke_worker":
            raise TransitionError("wrong_command_family")
        request = RevokeWorker.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.commands.register(command)
        reply = RuntimeReply(command, registered.operation_id)
        params = _bindings(command)

        def transaction(conn):
            # Guard prevents a new run appearing while we gather affected run locks.
            conn.execute(text("SELECT singleton FROM runtime.admission_guard WHERE singleton=true FOR UPDATE"))
            runs = conn.execute(text("SELECT * FROM runtime.runs WHERE " + SCOPE +
                " AND status IN ('running','blocked') ORDER BY run_id FOR UPDATE"), params).mappings().all()
            existing = self.leases._existing(conn, command)
            if existing is not None:
                return existing
            policy = self.leases._worker(conn, params, request.worker_id).revoke()
            conn.execute(text("UPDATE runtime.worker_policy SET revoked=true,revision=:revision WHERE " + SCOPE +
                " AND worker_id=:worker"), {**params, "worker": request.worker_id, "revision": policy.revision})
            for run in runs:
                binding = {**params, "run": run["run_id"], "worker": request.worker_id}
                lock_work(conn, binding)
                aborted = AbortDecision(registered.operation_id, request.reason_code).apply(conn, binding, request.worker_id)
                rows = conn.execute(text("SELECT a.*,v.current_fence,v.attempt_count,v.specification,v.status AS activation_status "
                    "FROM runtime.attempts a JOIN runtime.activations v USING (tenant_id,project_id,run_id,activation_id) "
                    "WHERE a.tenant_id=:tenant AND a.project_id=:project AND a.run_id=:run AND a.worker_id=:worker "
                    "AND a.status='leased' AND a.fence=v.current_fence ORDER BY a.activation_id"), binding).mappings().all()
                budget = RunBudget(run["budget_limit"], run["reserved"], run["spent"])
                changed = []
                for row in rows:
                    now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                    activation = ActivationState(row["activation_status"], row["current_fence"], row["attempt_count"],
                        run["input_snapshot"]["budget"]["max_attempts_per_activation"], row["specification"].get("side_effects", "pure"))
                    activation, lease, budget = activation.revoke(lease_from(row), budget, now=now,
                                                                  run=RunState(run["status"], run["revision"]))
                    conn.execute(text("UPDATE runtime.attempts SET status=:status,settled=:settled WHERE " + RUN +
                        " AND attempt_id=:attempt"), {**binding, "attempt": lease.attempt_id,
                                                       "status": lease.status, "settled": lease.settled})
                    conn.execute(text("UPDATE runtime.activations SET status=:status WHERE " + RUN +
                        " AND activation_id=:activation"), {**binding, "activation": row["activation_id"], "status": activation.status})
                    changed.append(lease.attempt_id)
                if changed or aborted:
                    operation = uuid.uuid5(uuid.UUID(registered.operation_id), run["run_id"]).hex
                    self.leases._changed(conn, binding, run, budget, operation,
                        {"kind": "worker_revoked", "worker_id": request.worker_id, "attempts": changed,
                         "aborted_intents": aborted, "policy_operation": registered.operation_id})
                    statuses = conn.execute(text("SELECT status FROM runtime.activations WHERE " + RUN), binding).scalars().all()
                    target = "blocked" if "uncertain" in statuses else "failed" if statuses and all(
                        s in {"failed", "cancelled", "succeeded", "abstained"} for s in statuses) and "failed" in statuses else run["status"]
                    conn.execute(text("UPDATE runtime.runs SET status=:status WHERE " + RUN), {**binding, "status": target})
                    queue_terminal(conn, binding, aborted)
            values = {**params, "worker": request.worker_id, "revision": policy.revision,
                "operation": registered.operation_id, "event": uuid.uuid4().hex,
                "payload": json.dumps({"kind": "worker_revoked", "worker_id": request.worker_id,
                    "revision": policy.revision, "reason_code": request.reason_code})}
            conn.execute(text("INSERT INTO runtime.policy_audit_events "
                "(event_id,tenant_id,project_id,worker_id,revision,operation_id,payload) VALUES "
                "(:event,:tenant,:project,:worker,:revision,:operation,CAST(:payload AS jsonb))"), values)
            conn.execute(text("INSERT INTO runtime.policy_outbox (operation_id,event_id,target,payload) "
                "VALUES (:operation,:event,'runtime_policy_notifications',CAST(:payload AS jsonb))"), values)
            return self.leases._finish(conn, command, reply.accepted("worker_policy", request.worker_id, policy.revision))
        return self.commands.transact(transaction)
