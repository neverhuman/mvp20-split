"""Read-only original publication outcomes for receipt-first client recovery."""

import json
from dataclasses import dataclass

from amphora_contracts_artifacts import (
    FinalizationAccepted,
    FinalizedReceipt,
    PublicationObservation,
    PublicationPending,
    PublicationRejected,
    UploadAccepted,
    UploadReceipt,
)
from amphora_contracts_commands import CommandIdentity
from sqlalchemy import text

from .model import UploadError


@dataclass(frozen=True, slots=True)
class PublicationRecord:
    identity: CommandIdentity
    operation_id: str
    request_digest: str
    outcome: PublicationPending | PublicationRejected | UploadAccepted | FinalizationAccepted

    @classmethod
    def from_row(cls, identity, row):
        if row["status"] == "pending":
            outcome = PublicationPending()
        elif row["status"] == "rejected":
            outcome = PublicationRejected(reason_code=row["receipt"]["reason_code"])
        elif identity.command_family == "artifacts.begin_upload":
            receipt = UploadReceipt.model_validate_json(json.dumps(row["receipt"]))
            if receipt.scope != identity.scope:
                raise UploadError("command_state_invalid")
            outcome = UploadAccepted(receipt=receipt)
        else:
            receipt = FinalizedReceipt.model_validate_json(json.dumps(row["receipt"]))
            if receipt.artifact.scope != identity.scope:
                raise UploadError("command_state_invalid")
            outcome = FinalizationAccepted(receipt=receipt)
        return cls(identity, row["operation_id"], row["request_sha256"], outcome)

    def to_wire(self):
        return PublicationObservation(identity=self.identity, operation_id=self.operation_id,
                                      request_sha256=self.request_digest, outcome=self.outcome)


class PublicationHistory:
    def __init__(self, engine):
        self.engine = engine

    def read(self, principal, family, command_id):
        actions = {"artifacts.begin_upload": "upload", "artifacts.finalize": "finalize"}
        if family not in actions:
            raise UploadError("command_unavailable")
        principal.require(actions[family])
        identity = CommandIdentity(command_family=family, command_id=command_id, scope=principal.scope, actor_id=principal.actor_id)
        with self.engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            row = connection.execute(text("SELECT status,receipt,operation_id,request_sha256 FROM artifacts.commands "
                "WHERE tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND family=:family AND command_id=:command"),
                {**principal.bindings, "family": family, "command": command_id}).mappings().one_or_none()
            if row is None:
                raise UploadError("command_unavailable")
            return PublicationRecord.from_row(identity, row).to_wire()
