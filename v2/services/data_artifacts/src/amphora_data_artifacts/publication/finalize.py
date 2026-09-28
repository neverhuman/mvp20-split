"""Verified immutable bytes precede an atomic catalog/receipt/audit/outbox commit."""

import json
import uuid
from dataclasses import dataclass

from amphora_contracts_artifacts import FinalizeArtifact, FinalizedReceipt
from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from ..persistence.commands import TerminalDisposition
from .model import UploadError
from .uploads import SCOPE


@dataclass(frozen=True, slots=True)
class ReadyPublication:
    request: FinalizeArtifact
    attempt_id: str
    generation: int
    key: str

    def receipt(self, principal, artifact_id):
        reference = ArtifactRef(artifact_id=artifact_id, scope=principal.scope,
                                **self.request.content.model_dump())
        return FinalizedReceipt(upload_id=self.request.upload_id, artifact=reference)


class Finalizer:
    def __init__(self, uploads, storage):
        self.uploads = uploads
        self.storage = storage

    def _existing(self, conn, principal, command):
        row = conn.execute(text("SELECT status,receipt FROM artifacts.commands WHERE " + SCOPE +
            " AND actor_id=:actor AND family='artifacts.finalize' AND command_id=:command"),
            {**principal.bindings, "command": command.identity.command_id}).mappings().one()
        return row["receipt"] if row["status"] != "pending" else None

    def _terminal(self, conn, principal, command, receipt, rejected=False):
        body = receipt if rejected else receipt.model_dump(mode="json")
        record = self.uploads.commands.finish(conn, command,
            TerminalDisposition("rejected" if rejected else "accepted", json.dumps(body).encode()))
        params = {**principal.bindings, "event": uuid.uuid4().hex, "operation": record.operation_id,
                  "payload": json.dumps({"kind": "finalization_rejected" if rejected else "artifact_finalized",
                                         "receipt": body})}
        conn.execute(text("INSERT INTO artifacts.audit_events "
            "(tenant_id,project_id,event_id,operation_id,ordinal,payload) VALUES "
            "(:tenant,:project,:event,:operation,0,CAST(:payload AS jsonb))"), params)
        if not rejected:
            conn.execute(text("INSERT INTO artifacts.outbox "
                "(tenant_id,project_id,operation_id,event_id,target,payload) VALUES "
                "(:tenant,:project,:operation,:event,'artifact_notifications',CAST(:payload AS jsonb))"), params)
        return body

    def _reject(self, conn, principal, command, error):
        return self._terminal(conn, principal, command,
            {"schema_version": "1", "status": "rejected", "reason_code": str(error)}, rejected=True)

    @staticmethod
    def _result(body):
        if body.get("status") == "rejected":
            raise UploadError(body["reason_code"])
        return FinalizedReceipt.model_validate_json(json.dumps(body))

    def finalize(self, principal, command):
        principal.require("finalize", command.identity)
        if command.identity.command_family != "artifacts.finalize":
            raise UploadError("wrong_command_family")
        request = FinalizeArtifact.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        self.uploads.commands.register(command)

        def prepare(conn):
            self.uploads._capacity(conn, principal)
            existing = self._existing(conn, principal, command)
            if existing is not None:
                return existing
            try:
                upload = self.uploads._upload(conn, principal, request.upload_id)
                if upload["expected_descriptor"] != request.content.model_dump(mode="json"):
                    raise UploadError("content_descriptor_conflict")
                self.uploads.policy.admit(request.content, self.uploads.limits)
                if upload["status"] not in {"provisional", "finalized"} or upload["selected_attempt"] is None:
                    raise UploadError("upload_not_ready")
                row = conn.execute(text("SELECT * FROM artifacts.upload_attempts WHERE " + SCOPE +
                    " AND upload_id=:upload AND attempt_id=:attempt"),
                    {**principal.bindings, "upload": request.upload_id,
                     "attempt": upload["selected_attempt"]}).mappings().one()
                if row["status"] != "streamed" or row["generation"] != upload["generation"]:
                    raise UploadError("upload_not_ready")
                return ReadyPublication(request, row["attempt_id"], row["generation"], row["storage_key"])
            except UploadError as error:
                return self._reject(conn, principal, command, error)

        ready = self.uploads.commands.transact(prepare)
        if isinstance(ready, dict):
            return self._result(ready)
        verification_error = None
        try:
            data = self.storage.verify(ready.key, request.content)
            self.uploads.policy.validate(request.content, data)
        except UploadError as error:
            verification_error = error
        # I/O failures propagate as retryable infrastructure errors; command remains pending.

        def commit(conn):
            self.uploads._capacity(conn, principal)
            upload = self.uploads._upload(conn, principal, request.upload_id)
            existing = self._existing(conn, principal, command)
            if existing is not None:
                return existing
            if verification_error is not None:
                return self._reject(conn, principal, command, verification_error)
            if (upload["selected_attempt"] != ready.attempt_id or upload["generation"] != ready.generation
                or upload["status"] not in {"provisional", "finalized"}):
                return self._reject(conn, principal, command, UploadError("upload_selection_changed"))
            params = {**principal.bindings, "key": ready.key, "upload": request.upload_id}
            if upload["status"] == "finalized":
                artifact_id = conn.execute(text("SELECT artifact_id FROM artifacts.catalog WHERE " + SCOPE +
                                                " AND storage_key=:key"), params).scalar_one()
            else:
                artifact_id = uuid.uuid4().hex
                content = request.content
                conn.execute(text("INSERT INTO artifacts.catalog "
                    "(tenant_id,project_id,artifact_id,content_sha256,size_bytes,media_type,schema_ref,storage_key) "
                    "VALUES (:tenant,:project,:artifact,:digest,:size,:media,CAST(:schema AS jsonb),:key)"),
                    {**params, "artifact": artifact_id, "digest": content.sha256, "size": content.size_bytes,
                     "media": content.media_type, "schema": content.schema_ref.model_dump_json()})
                conn.execute(text("UPDATE artifacts.uploads SET status='finalized' WHERE " + SCOPE +
                                  " AND upload_id=:upload"), params)
            # Selected bytes were already charged by upload settlement; no second catalog charge.
            return self._terminal(conn, principal, command, ready.receipt(principal, artifact_id))

        return self._result(self.uploads.commands.transact(commit))
