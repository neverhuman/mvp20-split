"""Resumable external reservation acquisition; acceptance is a separate owner gate."""

import json

from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_runtime import CommandReceipt
from sqlalchemy import text

from ..lifecycle.claims import SCOPE
from ..lifecycle.receipts import RuntimeReply
from ..persistence.commands import _bindings
from .artifacts import ReservationUnavailable, validate_receipt
from .prepare import IntentPreparation


class CompletionCoordinator:
    def __init__(self, engine, artifacts):
        self.preparation = IntentPreparation(engine, artifacts.owner)
        self.artifacts = artifacts
        self.engine = engine

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
                self.preparation.leases._run(conn, params)
                conn.execute(text("SELECT intent_id FROM runtime.completion_intents WHERE " + SCOPE +
                    " AND intent_id=:intent FOR UPDATE"), params).one()
                values = {**params, "output": key, "receipt": receipt.model_dump_json()}
                conn.execute(text("INSERT INTO runtime.intent_reservations "
                    "(tenant_id,project_id,intent_id,output_binding,receipt) VALUES "
                    "(:tenant,:project,:intent,:output,CAST(:receipt AS jsonb)) ON CONFLICT DO NOTHING"), values)
                actual = conn.execute(text("SELECT receipt FROM runtime.intent_reservations WHERE " + SCOPE +
                    " AND intent_id=:intent AND output_binding=:output"), values).scalar_one()
                if actual != receipt.model_dump(mode="json"):
                    raise ReservationUnavailable("reservation_receipt_conflict")
            self.preparation.commands.transact(store)
        # Recheck after remote I/O: cancellation/revocation may have permanently aborted the intent.
        current = self.preparation.prepare(principal, command)
        return current if isinstance(current, CommandReceipt) else RuntimeReply(command, prepared.intent_id).pending()
