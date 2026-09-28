"""Prepare immutable intent under live owner locks, before any artifact call."""

import json
import uuid

from sqlalchemy import text

from ..lifecycle.claims import SCOPE, RuntimeLeases, lease_from
from ..lifecycle.intents import AbortDecision
from ..lifecycle.model import RunBudget, RunState, TransitionError
from ..lifecycle.receipts import RuntimeReply
from ..persistence.commands import _bindings
from .model import CompletionProposal, PreparedIntent


class IntentPreparation:
    def __init__(self, engine, runtime_owner):
        self.leases = RuntimeLeases(engine)
        self.commands = self.leases.commands
        self.runtime_owner = runtime_owner

    def prepare(self, principal, command):
        principal.require("complete", command.identity)
        if command.identity.command_family != "runtime.complete":
            raise TransitionError("wrong_command_family")
        proposal = CompletionProposal.from_command(command)
        record = self.commands.register(command)
        reply = RuntimeReply(command, record.operation_id)
        prepared = PreparedIntent(record.operation_id, proposal, self.runtime_owner)
        request = proposal.request
        params = {**_bindings(command), "run": request.run_id, "attempt": request.completion.attempt_id,
                  "intent": prepared.intent_id}

        def transaction(conn):
            intent = None
            try:
                run = self.leases._run(conn, params)
                existing = self.leases._existing(conn, command)
                if existing is not None:
                    return existing
                authority = self.leases._worker(conn, params, principal.actor_id)
                row = conn.execute(text("SELECT a.*,v.current_fence,v.invocation_id,v.checkpoint_revision,v.specification "
                    "FROM runtime.attempts a JOIN runtime.activations v USING (tenant_id,project_id,run_id,activation_id) "
                    "WHERE a.tenant_id=:tenant AND a.project_id=:project AND a.run_id=:run AND a.attempt_id=:attempt "
                    "FOR UPDATE OF v,a"), params).mappings().one_or_none()
                intent = conn.execute(text("SELECT * FROM runtime.completion_intents WHERE " + SCOPE +
                    " AND intent_id=:intent FOR UPDATE"), params).mappings().one_or_none()
                if intent is not None and intent["status"] == "aborted":
                    raise TransitionError(intent["outcome"]["reason_code"])
                if row is None:
                    raise TransitionError("attempt_unavailable")
                if (row["invocation_id"], row["fence"]) != (request.completion.invocation_id, request.completion.fence):
                    raise TransitionError("stale_attempt")
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                lease_from(row).authorize(RunState(run["status"], run["revision"]), authority,
                    worker_id=principal.actor_id, attempt_id=request.completion.attempt_id,
                    current_fence=row["current_fence"], now=now)
                if request.expected_checkpoint_revision is not None and request.expected_checkpoint_revision != row["checkpoint_revision"]:
                    raise TransitionError("checkpoint_revision_conflict")
                proposal.validate_outputs(run["tool_snapshot"].get(row["invocation_id"]), row["specification"])
                if intent is not None:
                    if (intent["semantic_sha256"] != proposal.digest or
                        intent["output_bindings"] != prepared.stored_bindings()):
                        raise TransitionError("intent_binding_conflict")
                    return prepared
            except TransitionError as error:
                if intent is not None and intent["status"] == "prepared":
                    proof = AbortDecision(record.operation_id, str(error)).record()
                    conn.execute(text("UPDATE runtime.completion_intents SET status='aborted',outcome=CAST(:proof AS jsonb) "
                        "WHERE " + SCOPE + " AND intent_id=:intent AND status='prepared'"),
                        {**params, "proof": json.dumps(proof)})
                    self.leases._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
                        uuid.uuid5(uuid.UUID(record.operation_id), "abort").hex,
                        {"kind": "intent_aborted", "intent_id": prepared.intent_id, "reason_code": str(error)})
                return self.leases._finish(conn, command, reply.reject(str(error)))
            conn.execute(text("INSERT INTO runtime.completion_intents "
                "(tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence,operation_id,semantic_sha256,output_bindings,status) "
                "VALUES (:tenant,:project,:intent,:run,:activation,:attempt,:fence,:intent,:digest,CAST(:outputs AS jsonb),'prepared')"),
                {**params, "activation": row["activation_id"], "fence": row["fence"], "digest": proposal.digest,
                 "outputs": json.dumps(prepared.stored_bindings())})
            self.leases._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
                uuid.uuid5(uuid.UUID(record.operation_id), "prepare").hex,
                {"kind": "intent_prepared", "intent_id": prepared.intent_id, "semantic_sha256": proposal.digest})
            return prepared
        return self.commands.transact(transaction)
