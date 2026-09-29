"""One bounded scheduling pass over durable state; no external effects or peer I/O."""

import json

from amphora_contracts_campaigns import ActivationPath, ArtifactConstant
from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import GraphBinding
from sqlalchemy import text

from ..compiler import ActivationAddress
from ..lifecycle.claims import RUN
from ..lifecycle.model import TransitionError
from .aggregation import GraphAggregation
from .bindings import InvocationIntent
from .expansion import ScopeExpansion
from .materialization import InvocationMaterializer
from .predicates import PredicateValues
from .state import ScopeState, persist_node, persist_scope
from .values import BoundValues, ensure


class GraphPass:
    def __init__(self, conn, params, plan, graph, artifacts, waits):
        self.conn, self.params, self.plan, self.graph, self.artifacts = conn, params, plan, graph, artifacts
        self.order = graph["next_dispatch_order"]
        self.waits = waits
        self.aggregation = GraphAggregation(conn, params, plan, graph)
        self.expansion = ScopeExpansion(conn, params, plan, graph, artifacts, self.aggregation)

    def apply(self, maximum):
        changed = 0
        scopes = {}
        deferred = {}
        for _ in range(maximum):
            candidates = self.conn.execute(text("SELECT n.activation_id,n.scope_key,n.priority FROM runtime.graph_nodes n "
                "JOIN runtime.graph_scopes s USING (tenant_id,project_id,run_id,scope_key) "
                "WHERE n.tenant_id=:tenant AND n.project_id=:project AND n.run_id=:run "
                "AND s.status='active' AND n.status IN ('waiting','ready','issued')"), self.params).mappings().all()
            moved = False
            for candidate in sorted(candidates, key=lambda item: tuple(item["priority"])):
                if candidate["activation_id"] in deferred:
                    continue
                key = candidate["scope_key"]
                if key not in scopes:
                    scopes[key] = ScopeState.load(self.conn, self.params, self.plan, key)
                scope = scopes[key]
                row = next(row for row in scope.nodes.values() if row["activation_id"] == candidate["activation_id"])
                node = scope.definition(row)
                try:
                    # A permanent value failure rolls back only this node's attempted expansion.
                    with self.conn.begin_nested():
                        moved = self.step(scope, row, node)
                except TransitionError as error:
                    persist_node(self.conn, self.params, row, "blocked", reason=str(error))
                    if node.kind == "finish":
                        persist_scope(self.conn, self.params, key, "blocked")
                    moved = True
                if moved:
                    scopes.pop(key, None)
                    # Worker state cannot change while this transaction holds the run lock.
                    # Local dependencies and ancestor containers may become eligible after this step.
                    deferred = {identity: value for identity, value in deferred.items()
                        if value[0] not in {"scatter", "iterate"} and
                        not (value[1] == key and value[2] == "waiting")}
                    changed += 1
                    break
                deferred[row["activation_id"]] = (node.kind, key, row["status"])
            if not moved:
                break
        return changed

    def step(self, scope, row, node):
        if row["status"] == "waiting":
            deadline = node.kind == "join" and self.aggregation.expired(scope, node)
            status = scope.readiness(node, deadline=deadline)
            if status == "waiting":
                return False
            persist_node(self.conn, self.params, row, status,
                         reason="graph_dependency_unavailable" if status == "blocked" else None)
            if node.kind == "finish" and status in {"blocked", "skipped"}:
                persist_scope(self.conn, self.params, scope.address.key, status)
            return True
        if node.kind == "invoke":
            return self.invoke(scope, row, node)
        if node.kind == "await":
            return self.waits.step(scope, row, node)
        if node.kind in {"scatter", "iterate"}:
            return getattr(self.expansion, node.kind)(scope, row, node)
        if node.kind == "branch":
            route = "true" if PredicateValues(scope.environment, self.artifacts).evaluate(node.predicate) else "false"
            persist_node(self.conn, self.params, row, "succeeded", state={"route": route}, outputs=BoundValues(()))
        elif node.kind == "join":
            return self.aggregation.join(scope, row, node)
        elif node.kind == "finish":
            outputs = scope.environment.bind(node.outputs).validate(scope.body.outputs, self.plan.document.definition.scope)
            persist_node(self.conn, self.params, row, "succeeded", outputs=outputs)
            persist_scope(self.conn, self.params, scope.address.key, "completed", outputs)
        else:
            raise TransitionError("graph_node_unsupported")
        return True

    def invoke(self, scope, row, node):
        binding = {**self.params, "activation": row["activation_id"]}
        if row["status"] == "ready":
            active = self.conn.execute(text("SELECT count(*) FROM runtime.activations WHERE " + RUN +
                                            " AND status IN ('queued','leased')"), self.params).scalar_one()
            if active >= 256:
                return False
            path = ActivationPath.model_validate_json(json.dumps(row["path"]))
            address = ActivationAddress.for_plan(self.plan, path)
            InvocationMaterializer.apply(self.conn, self.params, InvocationIntent(address, node, scope.environment),
                                         self.order, self.graph["deadline"])
            self.order += 1
            return True
        activation = self.conn.execute(text("SELECT status FROM runtime.activations WHERE " + RUN +
                                             " AND activation_id=:activation"), binding).scalar_one()
        if activation in {"queued", "leased"}:
            return False
        if activation != "succeeded":
            accepted = self.conn.execute(text("SELECT result FROM runtime.accepted_completions WHERE " + RUN +
                " AND activation_id=:activation"), binding).scalar_one_or_none()
            state = row["state"] if accepted is None else {**row["state"], "tool_outcome": accepted["outcome"]}
            persist_node(self.conn, self.params, row, "failed", reason="tool_" + activation, state=state)
            return True
        result = self.conn.execute(text("SELECT result FROM runtime.accepted_completions WHERE " + RUN +
                                         " AND activation_id=:activation"), binding).scalar_one_or_none()
        ensure(result is not None and result["outcome"]["status"] == "succeeded", "graph_committed_result_missing")
        compiled = next(body for body in self.plan.document.scopes if body.path == scope.address.definition_path)
        ports = next(item.outputs for item in compiled.nodes if item.node_id == node.node_id)
        declarations = {port.name: port.value_type for port in ports}
        bindings = []
        for output in result["outcome"]["outputs"]:
            shape = declarations[output["port"]]
            artifact = ArtifactRef.model_validate_json(json.dumps(output["artifact"]))
            value = ArtifactConstant(kind="artifact", artifact=artifact, representation=shape.representation, unit=shape.unit)
            bindings.append(GraphBinding(port=output["port"], value=value))
        outputs = BoundValues(tuple(bindings)).validate(ports, self.plan.document.definition.scope)
        persist_node(self.conn, self.params, row, "succeeded", outputs=outputs)
        return True
