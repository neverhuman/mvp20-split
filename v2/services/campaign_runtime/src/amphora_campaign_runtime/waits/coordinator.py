"""Authenticated receipt delivery with outside-SQL protection and an atomic owner commit."""

import json
import uuid
from dataclasses import dataclass

from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_graph_runtime import SubmitDomainReceipt
from sqlalchemy import text

from ..completion.artifacts import ReservationUnavailable, validate_receipt
from ..completion.retention import queue_terminal
from ..lifecycle.claims import RUN, SCOPE, RuntimeLeases
from ..lifecycle.model import RunBudget, TransitionError
from ..lifecycle.receipts import RuntimeReply
from ..persistence.commands import _bindings
from .closures import WaitClosures, load_wait
from .disposition import WaitDisposition
from .intents import WaitIntents
from .model import ReceiptEvidence, ensure
from .preparation import WaitPreparation
from .retention import WaitRetentionIntent
from .storage import WaitRecords


@dataclass(frozen=True)
class ReceiptDelivery:
    command: object
    request: SubmitDomainReceipt
    operation_id: str

    @property
    def params(self):
        return {**_bindings(self.command), "run": self.request.run_id, "activation": self.request.activation_id}

    @property
    def reply(self):
        return RuntimeReply(self.command, self.operation_id)

    def evidence(self, conn, run):
        ensure(run["status"] == "running", "run_not_running")
        wait = load_wait(conn, self.params)
        ensure(self.request.expectation_sha256 == wait.sha256
               and self.request.wait_revision == wait.expectation.wait_revision, "wait_expectation_mismatch")
        evidence = ReceiptEvidence(self.request.receipt)
        WaitRecords.retain_receipt(conn, evidence)
        wait.validate_receipt(evidence)
        ensure(not conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.graph_wait_closures WHERE " + RUN +
            " AND activation_id=:activation)"), self.params).scalar_one(), "wait_already_closed")
        status = conn.execute(text("SELECT status FROM runtime.graph_nodes WHERE " + RUN +
            " AND activation_id=:activation"), self.params).scalar_one()
        ensure(status == "issued", "wait_not_open")
        ensure(conn.execute(text("SELECT clock_timestamp() < :deadline"), {"deadline": wait.deadline}).scalar_one(),
               "wait_deadline_expired")
        return wait, evidence


class WaitCoordinator:
    def __init__(self, engine, artifacts):
        self.leases, self.artifacts, self.engine = RuntimeLeases(engine), artifacts, engine
        self.intents = WaitIntents(self.leases)

    def submit(self, principal, command):
        principal.require("submit_receipt", command.identity)
        ensure(command.identity.command_family == "graph.submit_receipt", "wrong_command_family")
        request = SubmitDomainReceipt.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        ensure(request.receipt.issuer_id == principal.actor_id and request.receipt.scope == principal.scope,
               "wait_issuer_mismatch")
        registered = self.leases.commands.register(command)
        delivery = ReceiptDelivery(command, request, registered.operation_id)
        prepared = self.leases.commands.transact(lambda conn: self._prepare(conn, delivery))
        if not isinstance(prepared, WaitRetentionIntent):
            return prepared
        with self.engine.connect() as conn:
            raw = conn.execute(text("SELECT receipt FROM runtime.wait_intent_reservations WHERE " + SCOPE +
                " AND intent_id=:intent AND output_binding='result'"),
                {**delivery.params, "intent": prepared.intent_id}).scalar_one_or_none()
        if raw is None:
            try:
                receipt = self.artifacts.reserve(prepared.reservation)  # No owner transaction or locks.
                validate_receipt(prepared.reservation, receipt)
            except ReservationUnavailable:
                return delivery.reply.pending()
            self.leases.commands.transact(lambda conn: self._save(conn, delivery, prepared, receipt))
        else:
            validate_receipt(prepared.reservation, ReservationReceipt.model_validate_json(json.dumps(raw)))
        return self.leases.commands.transact(lambda conn: self._commit(conn, delivery))

    def _prepare(self, conn, delivery):
        run = None
        try:
            run = self.leases._run(conn, delivery.params)
            previous = self.leases._existing(conn, delivery.command)
            if previous is not None:
                return previous
            wait, evidence = delivery.evidence(conn, run)
            if evidence.receipt.outcome.status != "accepted":
                return self._close(conn, delivery, run, WaitDisposition.received(wait, evidence))
            intent = WaitRetentionIntent(wait, evidence, delivery.operation_id, self.artifacts.owner)
            WaitPreparation.prepare(conn, intent)
            return intent
        except TransitionError as error:
            return self._reject(conn, delivery, run, str(error))

    def _reject(self, conn, delivery, run, reason):
        if run is not None:
            aborted = self.intents.abort(conn, delivery.params, reason, operation=delivery.operation_id)
            if aborted:
                self._changed(conn, delivery, run, {"kind": "wait_delivery_aborted", "reason_code": reason})
                queue_terminal(conn, delivery.params, aborted)
        return self.leases._finish(conn, delivery.command, delivery.reply.reject(reason))

    def _changed(self, conn, delivery, run, event):
        return self.leases._changed(conn, delivery.params, run,
            RunBudget(run["budget_limit"], run["reserved"], run["spent"]), delivery.operation_id, event)

    def _save(self, conn, delivery, intent, receipt):
        run = self.leases._run(conn, delivery.params)
        params = {**delivery.params, "intent": intent.intent_id, "receipt": receipt.model_dump_json()}
        saved = conn.execute(text("INSERT INTO runtime.wait_intent_reservations "
            "(tenant_id,project_id,intent_id,output_binding,receipt) VALUES "
            "(:tenant,:project,:intent,'result',CAST(:receipt AS jsonb)) ON CONFLICT DO NOTHING RETURNING intent_id"),
            params).scalar_one_or_none()
        actual = conn.execute(text("SELECT receipt FROM runtime.wait_intent_reservations WHERE " + SCOPE +
            " AND intent_id=:intent AND output_binding='result'"), params).scalar_one()
        if actual != receipt.model_dump(mode="json"):
            raise ReservationUnavailable("reservation_receipt_conflict")
        status = conn.execute(text("SELECT status FROM runtime.wait_retention_intents WHERE " + SCOPE +
                                  " AND intent_id=:intent"), params).scalar_one()
        if saved is not None and status in {"committed", "aborted"}:
            operation = uuid.uuid5(uuid.NAMESPACE_URL, intent.intent_id + ":late-reservation").hex
            self.leases._changed(conn, delivery.params, run,
                RunBudget(run["budget_limit"], run["reserved"], run["spent"]), operation,
                {"kind": "late_wait_reservation_recorded", "intent_id": intent.intent_id})
            queue_terminal(conn, delivery.params, (intent.intent_id,))

    def _commit(self, conn, delivery):
        run = None
        try:
            run = self.leases._run(conn, delivery.params)
            previous = self.leases._existing(conn, delivery.command)
            if previous is not None:
                return previous
            wait, evidence = delivery.evidence(conn, run)
            intent = WaitRetentionIntent(wait, evidence, delivery.operation_id, self.artifacts.owner)
            prepared = WaitPreparation.prepare(conn, intent)
            ensure(prepared["status"] == "prepared", "wait_intent_not_prepared")
            # All tentative acceptance writes roll back if the final protection/deadline gate fails.
            with conn.begin_nested():
                conn.execute(text("UPDATE runtime.wait_retention_intents SET status='committed',outcome=CAST(:proof AS jsonb) "
                    "WHERE " + SCOPE + " AND intent_id=:intent"), {**delivery.params, "intent": intent.intent_id,
                    "proof": json.dumps({"status": "committed", "runtime_receipt_id": delivery.operation_id})})
                return self._close(conn, delivery, run, WaitDisposition.received(wait, evidence), intent.intent_id)
        except TransitionError as error:
            return self._reject(conn, delivery, run, str(error))

    def _close(self, conn, delivery, run, disposition, intent_id=None):
        WaitClosures.persist(conn, disposition, run["revision"] + 1, retention_intent=intent_id)
        aborted = self.intents.abort(conn, delivery.params, "wait_already_closed",
                                    activation=delivery.request.activation_id, keep=intent_id)
        revision = self._changed(conn, delivery, run, {"kind": "wait_closed",
            "activation_id": delivery.request.activation_id, "outcome": disposition.status})
        queue_terminal(conn, delivery.params, (*aborted, *((intent_id,) if intent_id else ())))
        return self.leases._finish(conn, delivery.command, delivery.reply.accepted("run", delivery.request.run_id, revision))
