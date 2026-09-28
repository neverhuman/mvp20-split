"""Runtime-only atomic acceptance; no external calls in this transaction."""

import json
import uuid

from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_tools import Succeeded
from sqlalchemy import text

from ..lifecycle.claims import RUN, SCOPE, RuntimeLeases, lease_from
from ..lifecycle.intents import AbortDecision
from ..lifecycle.model import RunBudget, RunState, TransitionError
from ..lifecycle.receipts import RuntimeReply
from ..persistence.commands import _bindings
from .artifacts import ReservationUnavailable, validate_receipt
from .decision import CompletionDecision
from .model import CompletionProposal, PreparedIntent
from .retention import queue_terminal


class CompletionCommitter:
    def __init__(self, engine, runtime_owner):
        self.leases = RuntimeLeases(engine)
        self.commands = self.leases.commands
        self.runtime_owner = runtime_owner

    def commit(self, principal, command):
        principal.require("complete", command.identity)
        if command.identity.command_family != "runtime.complete":
            raise TransitionError("wrong_command_family")
        record = self.commands.register(command)
        proposal = CompletionProposal.from_command(command)
        request = proposal.request
        prepared = PreparedIntent(record.operation_id, proposal, self.runtime_owner)
        reply = RuntimeReply(command, record.operation_id)
        params = {**_bindings(command), "run": request.run_id, "attempt": request.completion.attempt_id,
                  "intent": prepared.intent_id}

        def transaction(conn):
            intent = None
            try:
                run = self.leases._run(conn, params)
                existing = self.leases._existing(conn, command)
                if existing is not None:
                    return existing
                worker = self.leases._worker(conn, params, principal.actor_id)
                # Exhaustion may terminalize other queued activations; acquire those locks before any intent.
                conn.execute(text("SELECT activation_id FROM runtime.activations WHERE " + RUN +
                                  " ORDER BY activation_id FOR UPDATE"), params).all()
                row = conn.execute(text("SELECT a.*,v.current_fence,v.invocation_id,v.checkpoint_revision,v.specification,"
                    "v.status AS activation_status,v.attempt_count FROM runtime.attempts a JOIN runtime.activations v "
                    "USING (tenant_id,project_id,run_id,activation_id) WHERE a.tenant_id=:tenant AND a.project_id=:project "
                    "AND a.run_id=:run AND a.attempt_id=:attempt FOR UPDATE OF v,a"), params).mappings().one_or_none()
                intent = conn.execute(text("SELECT * FROM runtime.completion_intents WHERE " + SCOPE +
                    " AND intent_id=:intent FOR UPDATE"), params).mappings().one_or_none()
                if intent is not None and intent["status"] == "aborted":
                    raise TransitionError(intent["outcome"]["reason_code"])
                if row is None:
                    raise TransitionError("attempt_unavailable")
                if (row["invocation_id"], row["fence"]) != (request.completion.invocation_id, request.completion.fence):
                    raise TransitionError("stale_attempt")
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                lease_from(row).authorize(RunState(run["status"], run["revision"]), worker,
                    worker_id=principal.actor_id, attempt_id=request.completion.attempt_id,
                    current_fence=row["current_fence"], now=now)
                if request.expected_checkpoint_revision is not None and request.expected_checkpoint_revision != row["checkpoint_revision"]:
                    raise TransitionError("checkpoint_revision_conflict")
                proposal.validate_outputs(run["tool_snapshot"].get(row["invocation_id"]), row["specification"])
                if intent is None:
                    return reply.pending()
                if intent["status"] != "prepared":
                    raise RuntimeError("Terminal intent without terminal command")
                if intent["semantic_sha256"] != proposal.digest or intent["output_bindings"] != prepared.stored_bindings():
                    raise TransitionError("intent_binding_conflict")
                receipts = conn.execute(text("SELECT output_binding,receipt FROM runtime.intent_reservations WHERE " +
                    SCOPE + " AND intent_id=:intent ORDER BY output_binding"), params).mappings().all()
                expected = {r.intent.output_binding: r for r in prepared.reservations()}
                found = {r["output_binding"]: r["receipt"] for r in receipts}
                if set(found) - set(expected):
                    raise TransitionError("reservation_binding_mismatch")
                for key, body in found.items():
                    try:
                        validate_receipt(expected[key], ReservationReceipt.model_validate_json(json.dumps(body)))
                    except (ReservationUnavailable, ValueError) as error:
                        raise TransitionError("reservation_binding_mismatch") from error
                if set(found) != set(expected):
                    return reply.pending()
                # Re-read after all lock acquisition and receipt validation, immediately before the decision.
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                lease_from(row).authorize(RunState(run["status"], run["revision"]), worker,
                    worker_id=principal.actor_id, attempt_id=request.completion.attempt_id,
                    current_fence=row["current_fence"], now=now)
                decision = CompletionDecision.evaluate(proposal, run, row, worker, now)
            except TransitionError as error:
                if intent is not None and intent["status"] == "prepared":
                    conn.execute(text("UPDATE runtime.completion_intents SET status='aborted',outcome=CAST(:proof AS jsonb) "
                        "WHERE " + SCOPE + " AND intent_id=:intent AND status='prepared'"),
                        {**params, "proof": json.dumps(AbortDecision(record.operation_id, str(error)).record())})
                    self.leases._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
                        uuid.uuid5(uuid.UUID(record.operation_id), "abort").hex,
                        {"kind": "intent_aborted", "intent_id": prepared.intent_id, "reason_code": str(error)})
                    queue_terminal(conn, params, (prepared.intent_id,))
                return self.leases._finish(conn, command, reply.reject(str(error)))

            values = {**params, "activation": row["activation_id"], "fence": row["fence"],
                "result": request.completion.model_dump_json(), "reservations": json.dumps(list(found.values()))}
            conn.execute(text("INSERT INTO runtime.attempt_reports "
                "(tenant_id,project_id,report_id,intent_id,run_id,activation_id,attempt_id,fence,result,reservations) "
                "VALUES (:tenant,:project,:intent,:intent,:run,:activation,:attempt,:fence,CAST(:result AS jsonb),"
                "CAST(:reservations AS jsonb))"), values)
            if decision.canonical_result:
                conn.execute(text("INSERT INTO runtime.accepted_completions "
                    "(tenant_id,project_id,completion_id,intent_id,run_id,activation_id,attempt_id,fence,result,reservations) "
                    "VALUES (:tenant,:project,:intent,:intent,:run,:activation,:attempt,:fence,CAST(:result AS jsonb),"
                    "CAST(:reservations AS jsonb))"), values)
            outcome = request.completion.outcome
            if isinstance(outcome, Succeeded) and outcome.checkpoint is not None:
                checkpoint_revision = row["checkpoint_revision"] + 1
                conn.execute(text("INSERT INTO runtime.state_revisions "
                    "(tenant_id,project_id,run_id,activation_id,revision,completion_id,checkpoint) "
                    "VALUES (:tenant,:project,:run,:activation,:revision,:intent,CAST(:checkpoint AS jsonb))"),
                    {**values, "revision": checkpoint_revision, "checkpoint": outcome.checkpoint.model_dump_json()})
                conn.execute(text("UPDATE runtime.activations SET checkpoint_revision=:revision WHERE " + RUN +
                    " AND activation_id=:activation"), {**values, "revision": checkpoint_revision})
            conn.execute(text("UPDATE runtime.attempts SET status=:status,settled=:settled WHERE " + RUN +
                " AND attempt_id=:attempt"), {**values, "status": decision.lease.status, "settled": decision.lease.settled})
            conn.execute(text("UPDATE runtime.activations SET status=:status WHERE " + RUN +
                " AND activation_id=:activation"), {**values, "status": decision.activation.status})
            if decision.budget.available == 0:
                conn.execute(text("UPDATE runtime.activations SET status='failed' WHERE " + RUN +
                                  " AND status='queued'"), params)
            statuses = conn.execute(text("SELECT status FROM runtime.activations WHERE " + RUN), params).scalars().all()
            status = decision.run_status(statuses)
            conn.execute(text("UPDATE runtime.runs SET status=:status WHERE " + RUN), {**params, "status": status})
            conn.execute(text("UPDATE runtime.completion_intents SET status='committed',outcome=CAST(:proof AS jsonb) WHERE " +
                SCOPE + " AND intent_id=:intent"), {**params, "proof": json.dumps({"status": "committed",
                    "runtime_receipt_id": record.operation_id})})
            revision = self.leases._changed(conn, params, run, decision.budget, record.operation_id,
                {"kind": "completion_accepted", "completion_id": prepared.intent_id,
                 "attempt_id": row["attempt_id"], "outcome": outcome.status, "run_status": status})
            queue_terminal(conn, params, (prepared.intent_id,))
            return self.leases._finish(conn, command, reply.accepted("completion", prepared.intent_id, revision))
        return self.commands.transact(transaction)
