"""Explicit test-only owner-process barriers; no production fault switches."""

import json
import os
import sys

from amphora_capability_registry.catalog.model import Principal
from amphora_capability_registry.catalog.service import Registry
from amphora_capability_registry.descriptors.policy import PermissionPolicy
from amphora_capability_registry.descriptors.requirements import ResourceAllowance
from amphora_capability_registry.persistence.store import CommandStore
from amphora_contracts_tools import parse_registry_command
from sqlalchemy import create_engine


def emit(value):
    print(json.dumps(value), flush=True)


def barrier(stage, operation=None):
    emit({"stage": stage, "operation_id": operation, "pid": os.getpid()})
    if sys.stdin.readline().strip() != "continue":
        raise RuntimeError("Missing explicit test barrier release")


class PreparedBarrier(CommandStore):
    def apply(self, principal, command, handler):
        def held(connection, factory):
            receipt = handler(connection, factory)
            barrier("prepared", factory.operation_id)
            return receipt
        return super().apply(principal, command, held)


request = json.loads(sys.stdin.readline())
command = parse_registry_command(request["family"], json.dumps(request["command"]))
principal = Principal(command.identity.actor_id, command.identity.scope, frozenset(request["actions"]))
engine = create_engine(os.environ["AMPHORA_REGISTRY_DATABASE_URL"],
    connect_args={"application_name": request["application_name"], "options": "-c statement_timeout=15000"})
try:
    registry = Registry(engine, ResourceAllowance("x86_64", "windows", 2000, 1024, 0, 300, 8, 128), PermissionPolicy())
    if request.get("barrier") == "prepared":
        registry.commands = PreparedBarrier(engine)
    barrier("ready")
    receipt = registry.execute(principal, command)
    if request.get("barrier") == "committed":
        barrier("committed", receipt.operation_id)
    emit({"receipt": receipt.model_dump(mode="json")})
finally:
    engine.dispose()
