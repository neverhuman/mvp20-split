"""Atomic save/head/audit/receipt, with scoped draft locking and original replay."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_graph_runtime import DraftCommandReceipt, SaveDraft
from sqlalchemy import text

from ..lifecycle.model import TransitionError
from ..persistence.commands import WHERE, CommandStore, TerminalDisposition, _bindings
from . import storage
from .revisions import DraftConflict, DraftVersion


@dataclass(frozen=True, slots=True)
class DraftReply:
    command: object
    operation_id: str

    def receipt(self, outcome):
        return DraftCommandReceipt.model_validate({"outcome": {"binding": {
            "identity": self.command.identity.model_dump(), "request_sha256": self.command.sha256,
            "operation_id": self.operation_id}, **outcome}})

    def accepted(self, draft):
        return self.receipt({"status": "accepted", "committed": {"kind": "draft_revision", "object_id": draft.draft_id,
            "revision": draft.revision, "content_sha256": draft.content.sha256}})

    def rejected(self, reason):
        return self.receipt({"status": "rejected", "reason_code": reason})


class DefinitionCommands:
    def __init__(self, engine):
        self.commands = CommandStore(engine)

    def save(self, principal, command):
        principal.require("author", command.identity)
        if command.identity.command_family != "definition.save":
            raise TransitionError("wrong_command_family")
        request = SaveDraft.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        if request.definition.scope != principal.scope:
            raise TransitionError("access_denied")
        registered = self.commands.register(command)
        reply = DraftReply(command, registered.operation_id)
        params = {**_bindings(command), "draft": request.draft_id, "operation": registered.operation_id}
        lock_bytes = json.dumps(["definition-draft", params["tenant"], params["project"], params["draft"]], separators=(",", ":")).encode()
        lock = int.from_bytes(hashlib.sha256(lock_bytes).digest()[:8], "big", signed=True)

        def transaction(conn):
            existing = conn.execute(text("SELECT status,receipt FROM runtime.commands WHERE " + WHERE + " FOR UPDATE"), params).mappings().one()
            if existing["status"] != "pending":
                return DraftCommandReceipt.model_validate(existing["receipt"])
            # Serializes first creation as well as updates; collisions only delay unrelated drafts.
            conn.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
            current = storage.head(conn, params)
            try:
                draft = DraftVersion.save(request, current)
            except (DraftConflict, ValueError) as error:
                receipt = reply.rejected(str(error))
            else:
                storage.persist(conn, params, draft)
                receipt = reply.accepted(draft)
            self.commands.finish(conn, command, TerminalDisposition(receipt.outcome.status, receipt.model_dump_json().encode()))
            return receipt
        return self.commands.transact(transaction)
