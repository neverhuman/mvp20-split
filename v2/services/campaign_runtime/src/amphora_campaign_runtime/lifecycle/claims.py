"""Run-serialized claims and renewals; clocks read only after authority locks."""

import json
import uuid
from datetime import UTC, timedelta

from amphora_contracts_runtime import (
    ClaimInvocation,
    ClaimResponse,
    CommandReceipt,
    PreparedInvocation,
    RenewAttempt,
)
from amphora_contracts_tools import Invocation
from sqlalchemy import text

from ..persistence.commands import WHERE, CommandStore, TerminalDisposition, _bindings
from .model import ActivationState, AttemptLease, RunBudget, RunState, TransitionError, WorkerAuthority
from .receipts import RuntimeReply

SCOPE = "tenant_id=:tenant AND project_id=:project"
RUN = SCOPE + " AND run_id=:run"


def decoded(body):
    model = ClaimResponse if body["outcome"]["status"] in {"claimed", "no_eligible_work"} else CommandReceipt
    return model.model_validate_json(json.dumps(body))


def lease_from(row):
    return AttemptLease(row["attempt_id"], row["worker_id"], row["fence"], row["lease_expires_at"],
                        row["deadline"], row["status"], row["settled"])


class RuntimeLeases:
    def __init__(self, engine):
        self.commands = CommandStore(engine)

    def _finish(self, conn, command, receipt):
        disposition = "rejected" if receipt.outcome.status == "rejected" else "accepted"
        self.commands.finish(conn, command, TerminalDisposition(disposition, receipt.model_dump_json().encode()))
        return receipt

    def _run(self, conn, params):
        row = conn.execute(text("SELECT * FROM runtime.runs WHERE " + RUN + " FOR UPDATE"), params).mappings().one_or_none()
        if row is None:
            raise TransitionError("run_unavailable")
        return row

    def _worker(self, conn, params, worker_id):
        values = {**params, "worker": worker_id}
        conn.execute(text("INSERT INTO runtime.worker_policy (tenant_id,project_id,worker_id,revision,revoked) "
            "VALUES (:tenant,:project,:worker,0,false) ON CONFLICT DO NOTHING"), values)
        row = conn.execute(text("SELECT * FROM runtime.worker_policy WHERE " + SCOPE +
            " AND worker_id=:worker FOR UPDATE"), values).mappings().one()
        return WorkerAuthority(worker_id, row["revoked"], row["revision"])

    def _existing(self, conn, command):
        row = conn.execute(text("SELECT status,receipt FROM runtime.commands WHERE " + WHERE),
                           _bindings(command)).mappings().one()
        return decoded(row["receipt"]) if row["status"] != "pending" else None

    def _changed(self, conn, params, run, budget, operation, payload):
        revision = run["revision"] + 1
        values = {**params, "revision": revision, "reserved": budget.reserved, "spent": budget.spent,
                  "event": uuid.uuid4().hex, "operation": operation, "payload": json.dumps(payload)}
        conn.execute(text("UPDATE runtime.runs SET revision=:revision,reserved=:reserved,spent=:spent WHERE " + RUN), values)
        conn.execute(text("INSERT INTO runtime.audit_events (event_id,tenant_id,project_id,run_id,revision,ordinal,payload) "
            "VALUES (:event,:tenant,:project,:run,:revision,0,CAST(:payload AS jsonb))"), values)
        conn.execute(text("INSERT INTO runtime.outbox (operation_id,event_id,target,payload) "
            "VALUES (:operation,:event,'runtime_notifications',CAST(:payload AS jsonb))"), values)
        return revision

    def claim(self, principal, command):
        principal.require("claim", command.identity)
        if command.identity.command_family != "runtime.claim":
            raise TransitionError("wrong_command_family")
        request = ClaimInvocation.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        if request.worker_id != principal.actor_id:
            raise TransitionError("access_denied")
        record = self.commands.register(command)
        reply = RuntimeReply(command, record.operation_id)
        params = {**_bindings(command), "run": request.run_id}

        def transaction(conn):
            try:
                run = self._run(conn, params)
                existing = self._existing(conn, command)
                if existing is not None:
                    return existing
                state = RunState(run["status"], run["revision"])
                state.require_running()
                authority = self._worker(conn, params, request.worker_id)
                authority.require(request.worker_id)
            except TransitionError as error:
                return self._finish(conn, command, reply.reject(str(error)))
            budget = RunBudget(run["budget_limit"], run["reserved"], run["spent"])
            max_attempts = run["input_snapshot"]["budget"]["max_attempts_per_activation"]
            rows = conn.execute(text("SELECT * FROM runtime.activations WHERE " + RUN +
                " AND status IN ('queued','leased') AND specification->'tool'=CAST(:tool AS jsonb) "
                "ORDER BY activation_id FOR UPDATE"), {**params, "tool": request.tool.model_dump_json()}).mappings().all()
            now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
            expired = []
            chosen = None
            for row in rows:
                activation = ActivationState(row["status"], row["current_fence"], row["attempt_count"], max_attempts)
                binding = {**params, "activation": row["activation_id"]}
                if activation.status == "leased":
                    previous = conn.execute(text("SELECT * FROM runtime.attempts WHERE " + RUN +
                        " AND activation_id=:activation AND fence=:fence FOR UPDATE"),
                        {**binding, "fence": activation.fence}).mappings().one()
                    # Read the clock after all attempt locks too.
                    now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                    lease = lease_from(previous)
                    if now < lease.expires_at:
                        continue
                    activation, lease, budget = activation.terminal(lease, budget, "expired", now=now, run=state)
                    conn.execute(text("UPDATE runtime.attempts SET status='expired',settled=true WHERE " + RUN +
                        " AND attempt_id=:attempt"), {**params, "attempt": lease.attempt_id})
                    conn.execute(text("UPDATE runtime.activations SET status=:status WHERE " + RUN +
                        " AND activation_id=:activation"), {**binding, "status": activation.status})
                    expired.append(lease.attempt_id)
                deadline = row["deadline"] or now + timedelta(seconds=row["specification"]["timeout_seconds"])
                if activation.status == "queued" and budget.available and now < deadline:
                    chosen = (row, activation, deadline)
                    break
            if chosen is None:
                revision = self._changed(conn, params, run, budget, record.operation_id,
                    {"kind": "attempts_expired", "attempts": expired}) if expired else run["revision"]
                receipt = ClaimResponse.model_validate({"outcome": {"status": "no_eligible_work",
                    "receipt": reply.accepted("run", request.run_id, revision).outcome.model_dump()}})
                return self._finish(conn, command, receipt)
            row, activation, deadline = chosen
            now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
            try:
                activation, lease, budget = activation.claim(state, authority, budget, worker_id=request.worker_id,
                    attempt_id=uuid.uuid4().hex, now=now, deadline=deadline, seconds=request.lease_seconds)
            except TransitionError:
                # A deadline may pass while acquiring locks; rollback all expiry work and retry caller command.
                raise
            params2 = {**params, "activation": row["activation_id"], "attempt": lease.attempt_id,
                "fence": lease.fence, "worker": lease.worker_id, "expiry": lease.expires_at, "deadline": lease.deadline,
                "issued": activation.issued}
            conn.execute(text("INSERT INTO runtime.attempts (tenant_id,project_id,run_id,activation_id,attempt_id,fence,"
                "worker_id,lease_expires_at,deadline,status) VALUES (:tenant,:project,:run,:activation,:attempt,:fence,"
                ":worker,:expiry,:deadline,'leased')"), params2)
            conn.execute(text("UPDATE runtime.activations SET status='leased',current_fence=:fence,attempt_count=:issued,"
                "deadline=:deadline WHERE " + RUN + " AND activation_id=:activation"), params2)
            revision = self._changed(conn, params, run, budget, record.operation_id,
                {"kind": "attempt_claimed", "attempt_id": lease.attempt_id, "fence": lease.fence, "expired": expired})
            prepared = PreparedInvocation.model_validate_json(json.dumps(row["specification"]))
            invocation = Invocation(schema_version="1", scope=principal.scope, run_id=request.run_id,
                node_id=prepared.node_id, activation_id=prepared.activation_id, invocation_id=prepared.invocation_id,
                attempt_id=lease.attempt_id, fence=lease.fence, tool=prepared.tool, inputs=prepared.inputs,
                checkpoint=prepared.checkpoint, timeout_seconds=prepared.timeout_seconds, grant_id=lease.attempt_id)
            receipt = ClaimResponse.model_validate({"outcome": {"status": "claimed", "receipt":
                reply.accepted("attempt", lease.attempt_id, revision).outcome.model_dump(),
                "invocation": invocation.model_dump(), "lease_expires_at": lease.expires_at.astimezone(UTC).isoformat().replace("+00:00", "Z")}})
            return self._finish(conn, command, receipt)
        return self.commands.transact(transaction)

    def renew(self, principal, command):
        principal.require("renew", command.identity)
        if command.identity.command_family != "runtime.renew":
            raise TransitionError("wrong_command_family")
        request = RenewAttempt.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        record = self.commands.register(command)
        reply = RuntimeReply(command, record.operation_id)
        params = {**_bindings(command), "run": request.attempt.run_id, "attempt": request.attempt.attempt_id}

        def transaction(conn):
            try:
                run = self._run(conn, params)
                existing = self._existing(conn, command)
                if existing is not None:
                    return existing
                authority = self._worker(conn, params, principal.actor_id)
                row = conn.execute(text("SELECT a.*,v.current_fence,v.invocation_id FROM runtime.attempts a "
                    "JOIN runtime.activations v USING (tenant_id,project_id,run_id,activation_id) "
                    "WHERE a.tenant_id=:tenant AND a.project_id=:project AND a.run_id=:run AND a.attempt_id=:attempt "
                    "FOR UPDATE OF v,a"), params).mappings().one_or_none()
                if row is None:
                    raise TransitionError("attempt_unavailable")
                if row["invocation_id"] != request.attempt.invocation_id or row["fence"] != request.attempt.fence:
                    raise TransitionError("stale_attempt")
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                lease = lease_from(row).renew(RunState(run["status"], run["revision"]), authority,
                    worker_id=principal.actor_id, attempt_id=request.attempt.attempt_id,
                    current_fence=row["current_fence"], now=now, seconds=request.lease_seconds)
            except TransitionError as error:
                return self._finish(conn, command, reply.reject(str(error)))
            conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=:expiry WHERE " + RUN +
                              " AND attempt_id=:attempt"), {**params, "expiry": lease.expires_at})
            revision = self._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
                record.operation_id, {"kind": "attempt_renewed", "attempt_id": lease.attempt_id})
            return self._finish(conn, command, reply.accepted("attempt", lease.attempt_id, revision))
        return self.commands.transact(transaction)
