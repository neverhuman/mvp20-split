"""Derived begin command and immutable history; stream/finalize remain shared."""

import json
import uuid

from amphora_contracts_artifacts import (
    DerivedUploadAccepted,
    DerivedUploadObservation,
    DerivedUploadReceipt,
    PublicationPending,
    PublicationRejected,
    UploadReceipt,
)
from amphora_contracts_commands import CommandIdentity
from sqlalchemy import text

from ..persistence.commands import TerminalDisposition
from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from ..source_rights.ledger import SourceRights
from .ledger import DerivationLedger
from .model import DeclaredTransformation

FAMILY = "artifacts.begin_derived_upload"


class DerivedPublications:
    def __init__(self, uploads):
        self.uploads = uploads
        self.rights = SourceRights(uploads.commands.engine)

    def begin(self, principal, command):
        transformation = DeclaredTransformation.authorized(principal, command)
        content = transformation.request.content
        self.uploads.commands.register(command)

        def transaction(connection):
            self.rights.lock(connection, principal)
            capacity = self.uploads._capacity(connection, principal)
            params = principal.bindings | {"family": FAMILY, "command": command.identity.command_id}
            row = connection.execute(text("SELECT status,receipt FROM artifacts.commands WHERE " + SCOPE +
                " AND actor_id=:actor AND family=:family AND command_id=:command"), params).mappings().one()
            if row["status"] != "pending":
                return row["receipt"]
            try:
                DerivationLedger.check_inputs(connection, principal, transformation)
                self.rights.authorize(connection, principal, transformation.input_ids, use="process")
                self.uploads.policy.admit(content, self.uploads.limits)
                capacity.admit(self.uploads.limits, added_bytes=content.size_bytes, upload=True)
            except UploadError as error:
                body = {"schema_version": "1", "status": "rejected", "reason_code": str(error)}
                self.uploads.commands.finish(connection, command, TerminalDisposition("rejected", json.dumps(body).encode()))
                return body
            upload_id = uuid.uuid4().hex
            connection.execute(text("INSERT INTO artifacts.uploads "
                "(tenant_id,project_id,upload_id,actor_id,expected_descriptor,storage_key) "
                "VALUES (:tenant,:project,:upload,:actor,CAST(:descriptor AS jsonb),:key)"),
                params | {"upload": upload_id, "descriptor": content.model_dump_json(), "key": uuid.uuid4().hex})
            DerivationLedger.declare(connection, principal, transformation, upload_id)
            connection.execute(text("UPDATE artifacts.capacity SET charged_bytes=charged_bytes+:size,"
                "upload_count=upload_count+1 WHERE " + SCOPE), params | {"size": content.size_bytes})
            receipt = DerivedUploadReceipt(upload=UploadReceipt(upload_id=upload_id, scope=principal.scope, content=content),
                                           declaration=transformation.request.declaration)
            record = self.uploads.commands.finish(connection, command, TerminalDisposition("accepted", receipt.model_dump_json().encode()))
            connection.execute(text("INSERT INTO artifacts.audit_events "
                "(tenant_id,project_id,event_id,operation_id,ordinal,payload) "
                "VALUES (:tenant,:project,:event,:operation,0,CAST(:payload AS jsonb))"),
                params | {"event": uuid.uuid4().hex, "operation": record.operation_id,
                          "payload": json.dumps({"kind": "derived_upload_begun", "upload_id": upload_id})})
            return receipt.model_dump(mode="json")

        body = self.uploads.commands.transact(transaction)
        if body.get("status") == "rejected":
            raise UploadError(body["reason_code"])
        return DerivedUploadReceipt.model_validate_json(json.dumps(body))

    def history(self, principal, command_id):
        principal.require("upload")
        identity = CommandIdentity(command_family=FAMILY, command_id=command_id, scope=principal.scope, actor_id=principal.actor_id)
        with self.uploads.commands.engine.connect() as connection:
            row = connection.execute(text("SELECT status,receipt,operation_id,request_sha256 FROM artifacts.commands WHERE " + SCOPE +
                " AND actor_id=:actor AND family=:family AND command_id=:command"),
                principal.bindings | {"family": FAMILY, "command": command_id}).mappings().one_or_none()
        if row is None:
            raise UploadError("command_unavailable")
        if row["status"] == "pending":
            outcome = PublicationPending()
        elif row["status"] == "rejected":
            outcome = PublicationRejected(reason_code=row["receipt"]["reason_code"])
        else:
            receipt = DerivedUploadReceipt.model_validate_json(json.dumps(row["receipt"]))
            if receipt.upload.scope != principal.scope or any(ref.scope != principal.scope for ref in receipt.declaration.inputs):
                raise UploadError("derivation_state_invalid")
            outcome = DerivedUploadAccepted(receipt=receipt)
        return DerivedUploadObservation(identity=identity, operation_id=row["operation_id"],
                                        request_sha256=row["request_sha256"], outcome=outcome)

    def read(self, principal, artifact_id):
        with self.uploads.commands.engine.connect() as connection:
            return DerivationLedger.read(connection, principal, artifact_id)
