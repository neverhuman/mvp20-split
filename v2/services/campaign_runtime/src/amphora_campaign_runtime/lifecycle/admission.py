"""Exact synthetic fixture admission and installation-wide serialization."""

import json
import uuid
from dataclasses import dataclass
from types import MappingProxyType

from amphora_contracts_runtime import AdmitFixtureRun, CommandReceipt
from sqlalchemy import text

from ..persistence.commands import WHERE, CommandStore, TerminalDisposition, _bindings
from .model import RunBudget, TransitionError
from .receipts import RuntimeReply


@dataclass(frozen=True, slots=True)
class PreparedFixture:
    definition: AdmitFixtureRun

    def __post_init__(self):
        invocations = self.definition.invocations
        for field in ("activation_id", "invocation_id"):
            if len({getattr(i, field) for i in invocations}) != len(invocations):
                raise ValueError("Fixture execution identities must be unique")
        for invocation in invocations:
            if len({binding.port for binding in invocation.inputs}) != len(invocation.inputs):
                raise ValueError("Fixture input ports must be unique")
        RunBudget(self.definition.budget.limit)

    def verify(self, requested):
        if self.definition != requested:
            raise TransitionError("fixture_binding_conflict")


class FixtureCatalog:
    def __init__(self, definitions):
        definitions = tuple(definitions)
        entries = {d.fixture_id: PreparedFixture(d) for d in definitions}
        if not entries or len(entries) != len(definitions):
            raise ValueError("Nonempty unique explicit fixture allowlist required")
        self.entries = MappingProxyType(entries)

    def require(self, requested):
        fixture = self.entries.get(requested.fixture_id)
        if fixture is None:
            raise TransitionError("fixture_unavailable")
        fixture.verify(requested)
        return fixture


class FixtureAdmission:
    def __init__(self, engine, catalog):
        self.commands = CommandStore(engine)
        self.catalog = catalog

    def admit(self, principal, command):
        principal.require("admit", command.identity)
        if command.identity.command_family != "runtime.admit_fixture":
            raise TransitionError("wrong_command_family")
        request = AdmitFixtureRun.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.commands.register(command)
        reply = RuntimeReply(command, registered.operation_id)
        params = _bindings(command)

        def transaction(conn):
            conn.execute(text("SELECT singleton FROM runtime.admission_guard WHERE singleton=true FOR UPDATE"))
            existing = conn.execute(text("SELECT status,receipt FROM runtime.commands WHERE " + WHERE), params).mappings().one()
            if existing["status"] != "pending":
                return CommandReceipt.model_validate(existing["receipt"])
            try:
                fixture = self.catalog.require(request)
                if conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.runs WHERE status='running')")).scalar_one():
                    raise TransitionError("active_run_exists")
            except TransitionError as error:
                receipt = reply.reject(str(error))
                self.commands.finish(conn, command, TerminalDisposition("rejected", receipt.model_dump_json().encode()))
                return receipt
            definition = fixture.definition
            run_id = uuid.uuid4().hex
            binding = {**params, "run": run_id, "fixture": definition.fixture_id, "digest": definition.plan_sha256,
                       "snapshot": definition.model_dump_json(), "limit": definition.budget.limit}
            conn.execute(text("INSERT INTO runtime.runs (tenant_id,project_id,run_id,fixture_id,plan_sha256,"
                "input_snapshot,status,budget_limit) VALUES (:tenant,:project,:run,:fixture,:digest,"
                "CAST(:snapshot AS jsonb),'running',:limit)"), binding)
            for invocation in definition.invocations:
                conn.execute(text("INSERT INTO runtime.activations (tenant_id,project_id,run_id,activation_id,invocation_id,"
                    "specification,status) VALUES (:tenant,:project,:run,:activation,:invocation,CAST(:spec AS jsonb),'queued')"),
                    {**binding, "activation": invocation.activation_id, "invocation": invocation.invocation_id,
                     "spec": invocation.model_dump_json()})
            conn.execute(text("UPDATE runtime.admission_guard SET tenant_id=:tenant,project_id=:project,run_id=:run "
                              "WHERE singleton=true"), binding)
            event = {**binding, "event": uuid.uuid4().hex, "operation": registered.operation_id,
                     "payload": json.dumps({"kind": "fixture_admitted", "run_id": run_id, "fixture_id": definition.fixture_id})}
            conn.execute(text("INSERT INTO runtime.audit_events (event_id,tenant_id,project_id,run_id,revision,ordinal,payload) "
                "VALUES (:event,:tenant,:project,:run,0,0,CAST(:payload AS jsonb))"), event)
            conn.execute(text("INSERT INTO runtime.outbox (operation_id,event_id,target,payload) "
                "VALUES (:operation,:event,'runtime_notifications',CAST(:payload AS jsonb))"), event)
            receipt = reply.accepted("run", run_id, 0)
            self.commands.finish(conn, command, TerminalDisposition("accepted", receipt.model_dump_json().encode()))
            return receipt
        return self.commands.transact(transaction)
