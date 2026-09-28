"""Owner-private idempotency storage; domain handlers own receipt validation/authority."""

import json
import uuid
from dataclasses import dataclass
from typing import Literal

from amphora_contracts_commands import CanonicalCommand
from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError


class CommandConflict(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TerminalDisposition:
    status: Literal["accepted", "rejected"]
    receipt_bytes: bytes

    def __post_init__(self):
        if self.status not in ("accepted", "rejected"):
            raise ValueError("Terminal disposition required")
        if type(json.loads(self.receipt_bytes)) is not dict:
            raise ValueError("Validated owner receipt must be a JSON object")


@dataclass(frozen=True, slots=True)
class CommandRecord:
    operation_id: str
    status: str
    receipt_bytes: bytes | None

    @classmethod
    def from_row(cls, row):
        receipt = row["receipt"]
        return cls(row["operation_id"], row["status"], None if receipt is None else
                   json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())


def _bindings(command):
    identity = command.identity
    return {"tenant": identity.scope.tenant_id, "project": identity.scope.project_id,
            "actor": identity.actor_id, "family": identity.command_family, "command": identity.command_id}


WHERE = "tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND family=:family AND command_id=:command"


@dataclass(slots=True)
class CommandStore:
    engine: Engine

    def transact(self, operation):
        """Only short owner DB work belongs here; retries reload all state."""
        for attempt in range(3):
            try:
                with self.engine.begin() as connection:
                    return operation(connection)
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) not in {"40001", "40P01"} or attempt == 2:
                    raise
        raise AssertionError("Unreachable transaction retry")

    def register(self, command: CanonicalCommand) -> CommandRecord:
        bindings = {**_bindings(command), "operation": uuid.uuid4().hex,
                    "digest": command.sha256, "canonical": command.canonical_bytes}

        def operation(connection):
            connection.execute(text("INSERT INTO runtime.commands (tenant_id,project_id,actor_id,family,"
                                    "command_id,operation_id,profile,request_sha256,canonical_bytes) VALUES "
                                    "(:tenant,:project,:actor,:family,:command,:operation,'amphora-command-v1',"
                                    ":digest,:canonical) ON CONFLICT DO NOTHING"), bindings)
            row = connection.execute(text("SELECT * FROM runtime.commands WHERE " + WHERE), bindings).mappings().one()
            if row["request_sha256"] != command.sha256 or bytes(row["canonical_bytes"]) != command.canonical_bytes:
                raise CommandConflict("command_identity_conflict")
            return CommandRecord.from_row(row)

        return self.transact(operation)

    def finish(self, connection: Connection, command: CanonicalCommand,
               disposition: TerminalDisposition) -> CommandRecord:
        if not connection.in_transaction():
            raise ValueError("Caller-owned domain transaction required")
        bindings = _bindings(command)
        row = connection.execute(text("SELECT * FROM runtime.commands WHERE " + WHERE + " FOR UPDATE"),
                                 bindings).mappings().one()
        if row["request_sha256"] != command.sha256 or bytes(row["canonical_bytes"]) != command.canonical_bytes:
            raise CommandConflict("command_identity_conflict")
        if row["status"] != "pending":
            return CommandRecord.from_row(row)
        receipt = json.loads(disposition.receipt_bytes)
        connection.execute(text("UPDATE runtime.commands SET status=:status,receipt=CAST(:receipt AS jsonb),"
                                "terminal_at=clock_timestamp() WHERE " + WHERE),
                           {**bindings, "status": disposition.status, "receipt": json.dumps(receipt)})
        return CommandRecord(row["operation_id"], disposition.status,
                             json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode())
