"""Artifact-owned reservation transactions and public runtime proof handshake."""

import json
import uuid

from amphora_contracts_artifacts import (
    ConfirmRetention,
    ReconcileReservation,
    ReservationReceipt,
    ReserveArtifact,
)
from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from ..persistence.commands import WHERE, TerminalDisposition, _bindings
from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from .model import Reservation
from .outcomes import OutcomeUnavailable


class Reservations:
    def __init__(self, uploads, outcomes):
        self.uploads, self.outcomes = uploads, outcomes
        self.commands = uploads.commands

    def _existing(self, conn, command):
        row = conn.execute(text("SELECT status,receipt FROM artifacts.commands WHERE " + WHERE),
                           _bindings(command)).mappings().one()
        return row["receipt"] if row["status"] != "pending" else None

    def _record(self, conn, principal, command, body, rejected=False):
        record = self.commands.finish(conn, command,
            TerminalDisposition("rejected" if rejected else "accepted", json.dumps(body).encode()))
        params = {**principal.bindings, "operation": record.operation_id, "event": uuid.uuid4().hex,
                  "payload": json.dumps({"kind": command.identity.command_family, "receipt": body})}
        conn.execute(text("INSERT INTO artifacts.audit_events "
            "(tenant_id,project_id,event_id,operation_id,ordinal,payload) VALUES "
            "(:tenant,:project,:event,:operation,0,CAST(:payload AS jsonb))"), params)
        return body

    def _transaction(self, principal, command, action, *, receipt_model=ReservationReceipt):
        def execute(conn):
            self.uploads._capacity(conn, principal)
            previous = self._existing(conn, command)
            if previous is not None:
                return previous
            try:
                return self._record(conn, principal, command, action(conn).model_dump(mode="json"))
            except UploadError as error:
                return self._record(conn, principal, command,
                    {"schema_version": "1", "status": "rejected", "reason_code": str(error)}, rejected=True)
        body = self.commands.transact(execute)
        if body.get("status") == "rejected":
            raise UploadError(body["reason_code"])
        return receipt_model.model_validate(body)

    def _load(self, conn, principal, reservation_id, *, lock=True):
        row = conn.execute(text("SELECT r.*,c.size_bytes,c.media_type,c.schema_ref FROM artifacts.reservations r "
            "JOIN artifacts.catalog c USING (tenant_id,project_id,artifact_id,content_sha256) "
            "WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.reservation_id=:reservation "
            "AND r.runtime_owner=:actor" + (" FOR UPDATE OF r" if lock else "")),
            {**principal.bindings, "reservation": reservation_id}).mappings().one_or_none()
        if row is None:
            raise UploadError("reservation_unavailable")
        return Reservation.from_row(row, principal.scope)

    def get(self, principal, reservation_id):
        """Observe current protection without creating a command or changing state."""
        principal.require("retention")
        with self.commands.engine.connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            return self._load(conn, principal, reservation_id, lock=False).receipt()

    def reserve(self, principal, command):
        principal.require("retention", command.identity)
        if command.identity.command_family != "artifacts.reserve":
            raise UploadError("wrong_command_family")
        request = ReserveArtifact.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        if request.intent.runtime_owner != principal.actor_id:
            raise UploadError("access_denied")
        self.commands.register(command)

        def reserve(conn):
            reservation, _created = self._reserve_root(conn, principal, request)
            return reservation.receipt()
        return self._transaction(principal, command, reserve)

    def _reserve_root(self, conn, principal, request):
        """Owner transaction and scope capacity lock held; return exact root plus creation flag."""
        row = conn.execute(text("SELECT * FROM artifacts.catalog WHERE " + SCOPE + " AND artifact_id=:artifact"),
            {**principal.bindings, "artifact": request.artifact.artifact_id}).mappings().one_or_none()
        if row is None:
            raise UploadError("artifact_unavailable")
        stored = ArtifactRef(artifact_id=row["artifact_id"], scope=principal.scope, sha256=row["content_sha256"],
                             size_bytes=row["size_bytes"], media_type=row["media_type"], schema_ref=row["schema_ref"])
        if stored != request.artifact:
            raise UploadError("artifact_descriptor_conflict")
        params = {**principal.bindings, "intent": request.intent.intent_id, "output": request.intent.output_binding,
            "semantic": request.intent.semantic_completion_sha256, "artifact": stored.artifact_id,
            "digest": stored.sha256, "reservation": uuid.uuid4().hex}
        created = conn.execute(text("INSERT INTO artifacts.reservations "
            "(tenant_id,project_id,reservation_id,artifact_id,content_sha256,runtime_owner,intent_id,output_binding,semantic_sha256) "
            "VALUES (:tenant,:project,:reservation,:artifact,:digest,:actor,:intent,:output,:semantic) "
            "ON CONFLICT (tenant_id,project_id,runtime_owner,intent_id,output_binding) DO NOTHING "
            "RETURNING reservation_id"), params).scalar_one_or_none()
        reservation_id = conn.execute(text("SELECT reservation_id FROM artifacts.reservations WHERE " + SCOPE +
            " AND runtime_owner=:actor AND intent_id=:intent AND output_binding=:output"), params).scalar_one()
        reservation = self._load(conn, principal, reservation_id)
        if reservation.binding.artifact != stored or reservation.binding.intent != request.intent:
            raise UploadError("reservation_identity_conflict")
        return reservation, created is not None

    def reconcile(self, principal, command):
        principal.require("retention", command.identity)
        family = command.identity.command_family
        if family not in {"artifacts.confirm", "artifacts.reconcile"}:
            raise UploadError("wrong_command_family")
        model = ConfirmRetention if family == "artifacts.confirm" else ReconcileReservation
        request = model.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.commands.register(command)
        if registered.status != "pending":
            return self._transaction(principal, command, lambda conn: None)
        # A short read transaction ends before the authenticated remote request.
        with self.commands.engine.begin() as conn:
            reservation = self._load(conn, principal, request.reservation_id)
        if self.outcomes is None:
            raise OutcomeUnavailable("runtime_owner_unavailable")
        outcome = self.outcomes.lookup(reservation.binding)
        if outcome.proof.status in {"prepared", "unknown"}:
            raise OutcomeUnavailable("runtime_outcome_pending")

        def apply(conn):
            current = self._load(conn, principal, request.reservation_id)
            if family == "artifacts.confirm" and (request.intent_id != current.binding.intent.intent_id
                or outcome.proof.status != "committed" or request.runtime_receipt_id != outcome.proof.runtime_receipt_id):
                raise UploadError("confirmation_proof_mismatch")
            updated = current.apply(outcome)
            conn.execute(text("UPDATE artifacts.reservations SET status=:status,outcome_proof=CAST(:proof AS jsonb) "
                "WHERE " + SCOPE + " AND reservation_id=:reservation"),
                {**principal.bindings, "reservation": request.reservation_id, "status": updated.status,
                 "proof": json.dumps(updated.proof)})
            return updated.receipt()
        return self._transaction(principal, command, apply)
