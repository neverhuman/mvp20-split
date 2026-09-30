"""Compile immutable revisions outside transactions; commit evidence and original receipt together."""

import json
from types import MappingProxyType

from amphora_contracts_graph_runtime import DraftCommandReceipt, ValidateDraft
from sqlalchemy import text

from ..lifecycle.model import TransitionError
from ..persistence.commands import WHERE, CommandStore, TerminalDisposition, _bindings
from . import storage, validation_storage
from .commands import DraftReply


class DefinitionValidator:
    def __init__(self, engine, universes):
        self.commands = CommandStore(engine)
        if any(key != (universe.scope.tenant_id, universe.scope.project_id) for key, universe in universes.items()):
            raise ValueError("validation_universe_scope_mismatch")
        self.universes = MappingProxyType(dict(universes))

    def validate(self, principal, command):
        principal.require("validate", command.identity)
        if command.identity.command_family != "definition.validate":
            raise TransitionError("wrong_command_family")
        request = ValidateDraft.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.commands.register(command)
        params = {**_bindings(command), "draft": request.draft_id, "revision": request.revision,
                  "operation": registered.operation_id}
        reply = DraftReply(command, registered.operation_id)
        # Terminal replay remains available even after trusted configuration changes.
        with self.commands.engine.connect() as conn:
            row = conn.execute(text("SELECT status,receipt FROM runtime.commands WHERE " + WHERE), params).mappings().one()
            if row["status"] != "pending":
                return DraftCommandReceipt.model_validate(row["receipt"])
            draft = storage.version(conn.execute(text("SELECT * FROM runtime.definition_revisions WHERE " + storage.KEY +
                " AND revision=:revision"), params).mappings().one_or_none())
        universe = self.universes.get((principal.scope.tenant_id, principal.scope.project_id))
        reason = ("draft_unavailable" if draft is None else "draft_content_mismatch" if draft.content.sha256 != request.content_sha256
                  else "validation_universe_unavailable" if universe is None else None)
        result = None if reason else universe.validate(draft).to_wire(registered.operation_id)

        def transaction(conn):
            row = conn.execute(text("SELECT status,receipt FROM runtime.commands WHERE " + WHERE + " FOR UPDATE"), params).mappings().one()
            if row["status"] != "pending":
                return DraftCommandReceipt.model_validate(row["receipt"])
            if reason:
                receipt = reply.rejected(reason)
            else:
                validation_storage.persist(conn, params, universe, result)
                receipt = reply.receipt({"status": "accepted", "committed": {"kind": "draft_validation",
                    "object_id": result.validation_id, "revision": result.revision, "content_sha256": result.content_sha256}})
            self.commands.finish(conn, command, TerminalDisposition(receipt.outcome.status, receipt.model_dump_json().encode()))
            return receipt
        return self.commands.transact(transaction)
