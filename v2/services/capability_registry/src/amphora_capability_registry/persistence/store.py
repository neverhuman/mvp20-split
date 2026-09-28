"""Short scope-serialized owner transactions; no external work under SQL locks."""

import json
import uuid
from dataclasses import dataclass

from amphora_contracts_tools import RegistryReceipt
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..catalog.model import ReceiptFactory, RegistryDenied


def scope_bindings(scope):
    return {"tenant": scope.tenant_id, "project": scope.project_id}


@dataclass(slots=True)
class CommandStore:
    engine: object

    def apply(self, principal, command, handler):
        principal.authorize(command)
        identity = command.identity
        values = {**scope_bindings(identity.scope), "actor": identity.actor_id, "family": identity.command_family,
                  "command": identity.command_id, "digest": command.sha256, "canonical": command.canonical_bytes}
        for attempt in range(3):
            try:
                with self.engine.begin() as connection:
                    # First profile deliberately serializes short registry operations per scope.
                    # Hash collisions can only serialize unrelated scopes, never transfer authority.
                    key = json.dumps(["registry-v1", identity.scope.model_dump()], sort_keys=True)
                    connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"), {"key": key})
                    row = connection.execute(text("SELECT * FROM registry.commands WHERE tenant_id=:tenant AND project_id=:project "
                        "AND actor_id=:actor AND family=:family AND command_id=:command"), values).mappings().one_or_none()
                    if row is not None:
                        if row["request_sha256"] != command.sha256 or bytes(row["canonical_bytes"]) != command.canonical_bytes:
                            raise RegistryDenied("command_identity_conflict")
                        return RegistryReceipt.model_validate_json(json.dumps(row["receipt"]))
                    factory = ReceiptFactory(uuid.uuid4().hex)
                    receipt = handler(connection, factory)
                    receipt_json = receipt.model_dump_json()
                    connection.execute(text("INSERT INTO registry.commands (tenant_id,project_id,actor_id,family,command_id,"
                        "operation_id,request_sha256,canonical_bytes,receipt) VALUES "
                        "(:tenant,:project,:actor,:family,:command,:operation,:digest,:canonical,CAST(:receipt AS jsonb))"),
                        {**values, "operation": factory.operation_id, "receipt": receipt_json})
                    connection.execute(text("INSERT INTO registry.audit_events (tenant_id,project_id,operation_id,payload) "
                        "VALUES (:tenant,:project,:operation,CAST(:payload AS jsonb))"),
                        {**values, "operation": factory.operation_id, "payload": json.dumps({"family": identity.command_family,
                            "actor_id": identity.actor_id, "command_id": identity.command_id,
                            "status": receipt.status, "reason_code": receipt.reason_code})})
                    return receipt
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) not in {"40001", "40P01"} or attempt == 2:
                    raise
        raise AssertionError("Unreachable retry")
