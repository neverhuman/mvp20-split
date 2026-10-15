"""Recoverable command boundary: run lock, durable pass, receipt and notifications are atomic."""

import json

from amphora_contracts_campaigns import parse_execution_plan
from amphora_contracts_graph_runtime import AdvanceGraph
from sqlalchemy import text

from ..artifact_bindings.storage import BindingExecution, stop_bindings
from ..completion.retention import queue_terminal
from ..lifecycle.claims import RUN, RuntimeLeases
from ..lifecycle.model import TransitionError
from ..lifecycle.receipts import RuntimeReply
from ..lifecycle.settlement import BudgetSettlement
from ..persistence.commands import _bindings
from ..resource_profiles import InvocationCapacity
from ..completion.profiles import RetentionProfile
from ..waits.execution import WaitExecution, stop_waits
from .advancement import GraphPass
from .frontier import ScopeAddress
from .predicates import ProjectionNeeded
from .projections import ProjectionUnavailable
from .storage import GraphStorage
from .values import ensure


class GraphAdvancer:
    def __init__(self, engine, projections=None, bindings=None):
        self.leases, self.settlement, self.projections = RuntimeLeases(engine), BudgetSettlement(engine), projections
        self.bindings = bindings

    def advance(self, principal, command):
        principal.require("maintain", command.identity)
        ensure(command.identity.command_family == "graph.advance", "wrong_command_family")
        request = AdvanceGraph.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        registered = self.leases.commands.register(command)
        reply = RuntimeReply(command, registered.operation_id)
        params = {**_bindings(command), "run": request.run_id}
        artifacts = {}
        if self.bindings is not None:
            with self.leases.commands.engine.connect() as conn:
                previous = self.leases._existing(conn, command)
            if previous is not None:
                return previous
            self.bindings.tick(principal)

        def transaction(conn):
            try:
                run = self.leases._run(conn, params)
                existing = self.leases._existing(conn, command)
                if existing is not None:
                    return existing
                ensure(run["execution_mode"] == "graph", "graph_run_unavailable")
                ensure(run["status"] == "running", "run_not_running")
                InvocationCapacity.from_snapshot(run["input_snapshot"])
                RetentionProfile.from_snapshot(run["tool_snapshot"])
            except TransitionError as error:
                return self.leases._finish(conn, command, reply.reject(str(error)))
            graph = GraphStorage.graph(conn, params)
            document = conn.execute(text("SELECT document FROM runtime.graph_plans WHERE tenant_id=:tenant "
                "AND project_id=:project AND plan_sha256=:digest"), {**params, "digest": graph["plan_sha256"]}).scalar_one()
            plan = parse_execution_plan(json.dumps(document))
            waits = WaitExecution(conn, params, plan, graph, run, self.leases)
            bindings = BindingExecution(conn, params, plan, graph, run)
            expired = conn.execute(text("SELECT clock_timestamp() >= :deadline"), {"deadline": graph["deadline"]}).scalar_one()
            decision = self.settlement.apply(conn, params, run, stop=expired)
            changed, order = 0, graph["next_dispatch_order"]
            status, reason, outputs = decision.status, None, None
            if expired:
                status, reason = "blocked", "graph_deadline_exhausted"
            elif status == "running":
                machine = GraphPass(conn, params, plan, graph, artifacts, waits, bindings if self.bindings is not None else None)
                changed = machine.apply(request.max_transitions)
                order = machine.order
                root = conn.execute(text("SELECT status,outputs FROM runtime.graph_scopes WHERE " + RUN +
                    " AND scope_key=:scope"), {**params, "scope": ScopeAddress(plan.sha256).key}).mappings().one()
                if root["status"] != "active":
                    status = "completed" if root["status"] == "completed" else "blocked"
                    outputs = root["outputs"]
                    reason = None if status == "completed" else "graph_finish_unavailable"
                    # Partial closure can finish while independent pure work is still in flight.
                    settled_run = {**run, "reserved": decision.budget.reserved, "spent": decision.budget.spent}
                    decision = self.settlement.apply(conn, params, settled_run, stop=True)
                    if decision.status == "blocked":
                        status, reason, outputs = "blocked", "graph_uncertain_work", None
            if changed or decision.changed or status != run["status"]:
                if status in {"blocked", "completed"}:
                    bindings.terminal_intents.extend(stop_bindings(conn, params, run, reason or "graph_not_required_at_finish"))
                    waits.terminal_intents.extend(stop_waits(conn, params, run, self.leases,
                        reason or "graph_not_required_at_finish"))
                if status == "blocked":
                    conn.execute(text("UPDATE runtime.graph_nodes SET status='blocked',reason_code=:reason WHERE " + RUN +
                        " AND status IN ('waiting','ready','issued')"), {**params, "reason": reason or "graph_run_blocked"})
                    conn.execute(text("UPDATE runtime.graph_scopes SET status='blocked' WHERE " + RUN +
                                      " AND status='active'"), params)
                elif status == "completed":
                    conn.execute(text("UPDATE runtime.graph_nodes SET status='skipped',"
                        "reason_code='graph_not_required_at_finish' WHERE " + RUN +
                        " AND status IN ('waiting','ready','issued')"), params)
                    conn.execute(text("UPDATE runtime.graph_scopes SET status='skipped' WHERE " + RUN +
                                      " AND status='active'"), params)
                revision = self.leases._changed(conn, params, run, decision.budget, registered.operation_id,
                    {"kind": "graph_advanced", "transitions": changed, "status": status, "reason_code": reason})
                queue_terminal(conn, params, waits.terminal_intents)
                queue_terminal(conn, params, bindings.terminal_intents)
                conn.execute(text("UPDATE runtime.runs SET status=:status WHERE " + RUN), {**params, "status": status})
                conn.execute(text("UPDATE runtime.graph_runs SET frontier_revision=frontier_revision+1,"
                    "next_dispatch_order=:ordering,outputs=CAST(:outputs AS jsonb),stop_reason=:reason WHERE " + RUN),
                    {**params, "ordering": order, "outputs": None if outputs is None else json.dumps(outputs), "reason": reason})
            else:
                revision = run["revision"]
            return self.leases._finish(conn, command, reply.accepted("run", request.run_id, revision))

        # Missing immutable projections abort the SQL pass. Fetch without locks, then reconstruct from committed state.
        for _ in range(65):
            try:
                return self.leases.commands.transact(transaction)
            except ProjectionNeeded as needed:
                if self.projections is None or len(artifacts) >= 64:
                    raise ProjectionUnavailable("artifact_projection_capacity_unavailable") from needed
                try:
                    value = self.projections.fetch(needed.artifact)
                except TransitionError as error:
                    value = error
                artifacts[needed.artifact.model_dump_json()] = value
        raise ProjectionUnavailable("artifact_projection_capacity_unavailable")
