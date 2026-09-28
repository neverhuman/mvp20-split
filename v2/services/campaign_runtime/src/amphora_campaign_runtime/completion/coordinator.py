"""Resumable external reservation acquisition; acceptance is a separate owner gate."""

import json
import uuid

from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_runtime import CommandReceipt
from sqlalchemy import text

from ..lifecycle.claims import SCOPE
from ..lifecycle.model import RunBudget
from ..lifecycle.receipts import RuntimeReply
from ..persistence.commands import _bindings
from .artifacts import ReservationUnavailable, validate_receipt
from .commit import CompletionCommitter
from .prepare import IntentPreparation
from .retention import queue_terminal


class CompletionCoordinator:
    def __init__(self, engine, artifacts):
        self.preparation = IntentPreparation(engine, artifacts.owner)
        self.artifacts = artifacts
        self.engine = engine

    def complete(self, principal, command):
        receipt = self.prepare(principal, command)
        if receipt.outcome.status != "pending":
            return receipt
        return CompletionCommitter(self.engine, self.artifacts.owner).commit(principal, command)

    def prepare(self, principal, command):
        prepared = self.preparation.prepare(principal, command)
        if isinstance(prepared, CommandReceipt):
            return prepared
        params = {**_bindings(command), "intent": prepared.intent_id, "run": prepared.proposal.request.run_id}
        for reservation in prepared.reservations():
            key = reservation.intent.output_binding
            with self.engine.connect() as conn:
                cached = conn.execute(text("SELECT receipt FROM runtime.intent_reservations WHERE " + SCOPE +
                    " AND intent_id=:intent AND output_binding=:output"), {**params, "output": key}).scalar_one_or_none()
            if cached is not None:
                validate_receipt(reservation, ReservationReceipt.model_validate_json(json.dumps(cached)))
                continue
            try:
                receipt = self.artifacts.reserve(reservation)  # No owner transaction or lock is open here.
                validate_receipt(reservation, receipt)
            except ReservationUnavailable:
                return RuntimeReply(command, prepared.intent_id).pending()
            def store(conn, key=key, receipt=receipt):
                run = self.preparation.leases._run(conn, params)
                intent = conn.execute(text("SELECT status FROM runtime.completion_intents WHERE " + SCOPE +
                    " AND intent_id=:intent FOR UPDATE"), params).mappings().one()
                values = {**params, "output": key, "receipt": receipt.model_dump_json()}
                inserted = conn.execute(text("INSERT INTO runtime.intent_reservations "
                    "(tenant_id,project_id,intent_id,output_binding,receipt) VALUES "
                    "(:tenant,:project,:intent,:output,CAST(:receipt AS jsonb)) ON CONFLICT DO NOTHING RETURNING output_binding"), values).scalar_one_or_none()
                actual = conn.execute(text("SELECT receipt FROM runtime.intent_reservations WHERE " + SCOPE +
                    " AND intent_id=:intent AND output_binding=:output"), values).scalar_one()
                if actual != receipt.model_dump(mode="json"):
                    raise ReservationUnavailable("reservation_receipt_conflict")
                if inserted is not None and intent["status"] in {"aborted", "committed"}:
                    operation = uuid.uuid5(uuid.UUID(prepared.intent_id), "late-reservation:" + key).hex
                    self.preparation.leases._changed(conn, params, run,
                        RunBudget(run["budget_limit"], run["reserved"], run["spent"]), operation,
                        {"kind": "late_reservation_recorded", "intent_id": prepared.intent_id, "output_binding": key})
                    queue_terminal(conn, params, (prepared.intent_id,))
            self.preparation.commands.transact(store)
        # Recheck after remote I/O: cancellation/revocation may have permanently aborted the intent.
        current = self.preparation.prepare(principal, command)
        return current if isinstance(current, CommandReceipt) else RuntimeReply(command, prepared.intent_id).pending()
