"""Owner transactions for provisional uploads; no filesystem work under SQL locks."""

import json
import uuid

from amphora_contracts_artifacts import ContentDescriptor, UploadReceipt
from sqlalchemy import text

from ..persistence.commands import CommandStore, TerminalDisposition
from .model import Capacity, UploadAttempt, UploadError

SCOPE = "tenant_id=:tenant AND project_id=:project"


class Uploads:
    def __init__(self, engine, limits, policy):
        self.commands = CommandStore(engine)
        self.limits = limits
        self.policy = policy

    def _capacity(self, conn, principal):
        conn.execute(text("INSERT INTO artifacts.capacity (tenant_id,project_id) VALUES (:tenant,:project) "
                          "ON CONFLICT DO NOTHING"), principal.bindings)
        row = conn.execute(text("SELECT * FROM artifacts.capacity WHERE " + SCOPE + " FOR UPDATE"),
                           principal.bindings).mappings().one()
        return Capacity.from_row(row)

    def _upload(self, conn, principal, upload_id):
        row = conn.execute(text("SELECT * FROM artifacts.uploads WHERE " + SCOPE +
                                " AND upload_id=:upload AND actor_id=:actor FOR UPDATE"),
                           {**principal.bindings, "upload": upload_id}).mappings().one_or_none()
        if row is None:
            raise UploadError("upload_unavailable")
        return row

    def begin(self, principal, command):
        principal.require("upload", command.identity)
        if command.identity.command_family != "artifacts.begin_upload":
            raise UploadError("wrong_command_family")
        # Public family parser validated the payload; reconstruct from immutable bytes.
        content = ContentDescriptor.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]["content"]))
        self.commands.register(command)

        def transaction(conn):
            capacity = self._capacity(conn, principal)
            params = {**principal.bindings, "command": command.identity.command_id}
            stored = conn.execute(text("SELECT status,receipt FROM artifacts.commands WHERE " + SCOPE +
                " AND actor_id=:actor AND family='artifacts.begin_upload' AND command_id=:command"), params).mappings().one()
            if stored["status"] != "pending":
                return stored["receipt"]
            try:
                self.policy.admit(content, self.limits)
                capacity.admit(self.limits, added_bytes=content.size_bytes, upload=True)
            except UploadError as error:
                receipt = {"schema_version": "1", "status": "rejected", "reason_code": str(error)}
                self.commands.finish(conn, command, TerminalDisposition("rejected", json.dumps(receipt).encode()))
                return receipt
            upload_id = uuid.uuid4().hex
            conn.execute(text("INSERT INTO artifacts.uploads "
                "(tenant_id,project_id,upload_id,actor_id,expected_descriptor,storage_key) VALUES "
                "(:tenant,:project,:upload,:actor,CAST(:descriptor AS jsonb),:key)"),
                {**params, "upload": upload_id, "descriptor": content.model_dump_json(), "key": uuid.uuid4().hex})
            conn.execute(text("UPDATE artifacts.capacity SET charged_bytes=charged_bytes+:size,"
                              "upload_count=upload_count+1 WHERE " + SCOPE),
                         {**params, "size": content.size_bytes})
            receipt = UploadReceipt(upload_id=upload_id, scope=principal.scope, content=content)
            record = self.commands.finish(conn, command, TerminalDisposition("accepted", receipt.model_dump_json().encode()))
            conn.execute(text("INSERT INTO artifacts.audit_events "
                "(tenant_id,project_id,event_id,operation_id,ordinal,payload) VALUES "
                "(:tenant,:project,:event,:operation,0,CAST(:payload AS jsonb))"),
                {**params, "event": uuid.uuid4().hex, "operation": record.operation_id,
                 "payload": json.dumps({"kind": "upload_begun", "upload_id": upload_id})})
            return receipt.model_dump(mode="json")

        receipt = self.commands.transact(transaction)
        if receipt.get("status") == "rejected":
            raise UploadError(receipt["reason_code"])
        return UploadReceipt.model_validate_json(json.dumps(receipt))

    def start(self, principal, upload_id):
        principal.require("upload")

        def transaction(conn):
            capacity = self._capacity(conn, principal)
            upload = self._upload(conn, principal, upload_id)
            if upload["status"] != "provisional":
                raise UploadError("upload_not_provisional")
            if upload["generation"] >= self.limits.attempts:
                raise UploadError("attempt_limit")
            content = ContentDescriptor.model_validate_json(json.dumps(upload["expected_descriptor"]))
            # The first attempt consumes the reservation made by BeginUpload.
            additional = content.size_bytes if upload["generation"] else 0
            capacity.admit(self.limits, added_bytes=additional, stream=True)
            attempt = UploadAttempt(upload_id, uuid.uuid4().hex, upload["generation"] + 1,
                                    uuid.uuid4().hex, content)
            params = {**principal.bindings, "upload": upload_id, "attempt": attempt.attempt_id,
                      "generation": attempt.generation, "key": attempt.storage_key,
                      "size": content.size_bytes, "additional": additional, "seconds": self.limits.seconds}
            conn.execute(text("INSERT INTO artifacts.upload_attempts "
                "(tenant_id,project_id,upload_id,attempt_id,generation,storage_key,allocated_bytes,expires_at) "
                "VALUES (:tenant,:project,:upload,:attempt,:generation,:key,:size,"
                "clock_timestamp()+make_interval(secs => :seconds))"), params)
            conn.execute(text("UPDATE artifacts.uploads SET generation=:generation,selected_attempt=NULL,"
                              "bytes_received=0 WHERE " + SCOPE + " AND upload_id=:upload"), params)
            conn.execute(text("UPDATE artifacts.capacity SET active_streams=active_streams+1,"
                              "charged_bytes=charged_bytes+:additional WHERE " + SCOPE), params)
            return attempt

        return self.commands.transact(transaction)

    def finish(self, principal, attempt, *, verified, actual_bytes=None):
        """Settle only a closed writer; unknown byte count conservatively retains allocation."""
        principal.require("upload")

        def transaction(conn):
            self._capacity(conn, principal)
            upload = self._upload(conn, principal, attempt.upload_id)
            params = {**principal.bindings, "upload": attempt.upload_id, "attempt": attempt.attempt_id}
            row = conn.execute(text("SELECT * FROM artifacts.upload_attempts WHERE " + SCOPE +
                " AND upload_id=:upload AND attempt_id=:attempt FOR UPDATE"), params).mappings().one()
            if row["status"] != "streaming":
                return row["status"]
            count = row["allocated_bytes"] if actual_bytes is None else actual_bytes
            if type(count) is not int or not 0 <= count <= row["allocated_bytes"]:
                raise UploadError("invalid_byte_settlement")
            unexpired = conn.execute(text("SELECT clock_timestamp() < :expiry"),
                                    {"expiry": row["expires_at"]}).scalar_one()
            current = upload["status"] == "provisional" and upload["generation"] == row["generation"]
            status = "streamed" if verified and current and unexpired else ("stale" if not current else "failed")
            if verified and count != row["allocated_bytes"]:
                raise UploadError("invalid_byte_settlement")
            conn.execute(text("UPDATE artifacts.upload_attempts SET status=:status,actual_bytes=:count WHERE " +
                              SCOPE + " AND upload_id=:upload AND attempt_id=:attempt"),
                         {**params, "status": status, "count": count})
            conn.execute(text("UPDATE artifacts.capacity SET active_streams=active_streams-1,"
                              "charged_bytes=charged_bytes-:refund WHERE " + SCOPE),
                         {**params, "refund": row["allocated_bytes"] - count})
            if status == "streamed":
                conn.execute(text("UPDATE artifacts.uploads SET selected_attempt=:attempt,bytes_received=:count WHERE " +
                                  SCOPE + " AND upload_id=:upload"), {**params, "count": count})
            return status

        return self.commands.transact(transaction)
