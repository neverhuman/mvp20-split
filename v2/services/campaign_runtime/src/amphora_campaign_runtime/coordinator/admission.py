"""Exact reviewed graph admission; plan/frontier/receipt commit under the existing guard."""

import json
import uuid
from datetime import timedelta

from amphora_contracts_graph_runtime import AdmitGraphRun
from amphora_contracts_runtime import CommandReceipt
from sqlalchemy import text

from ..lifecycle.model import RunBudget, TransitionError
from ..lifecycle.pins import PinnedTools
from ..lifecycle.receipts import RuntimeReply
from ..persistence.commands import WHERE, CommandStore, TerminalDisposition, _bindings
from .bindings import InvocationIntent, ValueEnvironment
from .frontier import FrontierPlanner, ScopeAddress
from .materialization import InvocationMaterializer
from .storage import GraphStorage
from .values import BoundValues, ensure


class GraphAdmission:
    def __init__(self, engine, catalog, *, bindings_enabled=False):
        self.commands, self.catalog = CommandStore(engine), catalog
        self.bindings_enabled = bindings_enabled

    def admit(self, principal, command):
        principal.require("admit", command.identity)
        ensure(command.identity.command_family == "graph.admit", "wrong_command_family")
        request = AdmitGraphRun.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.commands.register(command)
        reply = RuntimeReply(command, registered.operation_id)
        params = _bindings(command)

        def transaction(conn):
            conn.execute(text("SELECT singleton FROM runtime.admission_guard WHERE singleton=true FOR UPDATE"))
            existing = conn.execute(text("SELECT status,receipt FROM runtime.commands WHERE " + WHERE), params).mappings().one()
            if existing["status"] != "pending":
                return CommandReceipt.model_validate(existing["receipt"])
            try:
                entry = self.catalog.require(principal.scope, request.plan_sha256)
                ensure(entry.plan.schema_version != "4" or self.bindings_enabled, "graph_binding_profile_not_enabled")
                values = BoundValues(request.inputs).validate(entry.plan.document.definition.body.inputs, principal.scope)
                RunBudget(request.budget.limit)
                address = ScopeAddress(entry.plan.sha256)
                intents = FrontierPlanner().scope(entry.plan, address)
                ensure(len(intents) <= request.limits.max_activations, "graph_activation_limit")
                ensure(not conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.runs WHERE status='running')")).scalar_one(),
                       "active_run_exists")
            except TransitionError as error:
                receipt = reply.reject(str(error))
                self.commands.finish(conn, command, TerminalDisposition("rejected", receipt.model_dump_json().encode()))
                return receipt
            GraphStorage.retain_plan(conn, params, entry)
            run_id = uuid.uuid4().hex
            deadline = conn.execute(text("SELECT clock_timestamp()")).scalar_one() + timedelta(seconds=request.limits.deadline_seconds)
            binding = {**params, "run": run_id, "campaign": entry.plan.document.definition.campaign_id,
                "digest": entry.plan.sha256, "snapshot": request.model_dump_json(), "limit": request.budget.limit,
                "tools": json.dumps(PinnedTools(entry.descriptors).graph_snapshot()), "inputs": json.dumps(values.record()),
                "maximum": request.limits.max_activations, "deadline": deadline}
            conn.execute(text("INSERT INTO runtime.runs (tenant_id,project_id,run_id,fixture_id,plan_sha256,input_snapshot,"
                "status,budget_limit,tool_snapshot,execution_mode) VALUES (:tenant,:project,:run,:campaign,:digest,"
                "CAST(:snapshot AS jsonb),'running',:limit,CAST(:tools AS jsonb),'graph')"), binding)
            conn.execute(text("INSERT INTO runtime.graph_runs (tenant_id,project_id,run_id,plan_sha256,inputs,max_activations,deadline) "
                "VALUES (:tenant,:project,:run,:digest,CAST(:inputs AS jsonb),:maximum,:deadline)"), binding)
            GraphStorage.create_scope(conn, binding, address, values, intents)
            nodes = {node.node_id: node for node in entry.plan.document.definition.body.nodes}
            environment = ValueEnvironment(values, {})
            issued = 0
            for intent in intents:
                if intent.kind == "invoke" and intent.status == "ready":
                    InvocationMaterializer.apply(conn, binding,
                        InvocationIntent(intent.address, nodes[intent.address.path.node_id], environment), issued, deadline)
                    issued += 1
            conn.execute(text("UPDATE runtime.graph_runs SET next_dispatch_order=:issued WHERE tenant_id=:tenant "
                              "AND project_id=:project AND run_id=:run"), {**binding, "issued": issued})
            conn.execute(text("UPDATE runtime.admission_guard SET tenant_id=:tenant,project_id=:project,run_id=:run WHERE singleton=true"), binding)
            event = {**binding, "event": uuid.uuid4().hex, "operation": registered.operation_id,
                     "payload": json.dumps({"kind": "graph_admitted", "run_id": run_id, "plan_sha256": entry.plan.sha256,
                                            "nodes": len(intents), "issued_invocations": issued})}
            conn.execute(text("INSERT INTO runtime.audit_events (event_id,tenant_id,project_id,run_id,revision,ordinal,payload) "
                "VALUES (:event,:tenant,:project,:run,0,0,CAST(:payload AS jsonb))"), event)
            conn.execute(text("INSERT INTO runtime.outbox (operation_id,event_id,target,payload) "
                "VALUES (:operation,:event,'runtime_notifications',CAST(:payload AS jsonb))"), event)
            receipt = reply.accepted("run", run_id, 0)
            self.commands.finish(conn, command, TerminalDisposition("accepted", receipt.model_dump_json().encode()))
            return receipt
        return self.commands.transact(transaction)
