"""Nested scope transitions with frozen membership and append-only iteration checkpoints."""

import json

from amphora_contracts_campaigns import ActivationPath
from amphora_contracts_graph_runtime import CollectionValue, GraphBinding
from sqlalchemy import text

from ..lifecycle.claims import RUN
from .bindings import ValueEnvironment
from .collections import FrozenMembership
from .frontier import FrontierPlanner, ScopeAddress
from .predicates import PredicateValues
from .state import persist_node
from .storage import GraphStorage
from .values import BoundValues, ensure


class ScopeExpansion:
    def __init__(self, conn, params, plan, graph, artifacts, aggregation):
        self.conn, self.params, self.plan, self.graph, self.artifacts = conn, params, plan, graph, artifacts
        self.aggregation = aggregation

    def children(self, row):
        rows = self.conn.execute(text("SELECT * FROM runtime.graph_scopes WHERE " + RUN +
            " AND parent_activation_id=:parent"), {**self.params, "parent": row["activation_id"]}).mappings().all()
        return sorted(rows, key=lambda child: child["occurrences"][-1]["index"])

    def create(self, scope, row, node, index, inputs, membership=None):
        occurrence = {"kind": "loop" if node.kind == "iterate" else "scatter", "node_id": node.node_id, "index": index}
        if membership is not None:
            occurrence["membership_sha256"] = membership
        path = ActivationPath.model_validate_json(json.dumps({"schema_version": "2", "node_id": node.node_id,
            "occurrences": [item.model_dump(mode="json") for item in scope.address.occurrences] + [occurrence]}))
        address = ScopeAddress(self.plan.sha256, path.occurrences)
        intents = FrontierPlanner().scope(self.plan, address)
        count = self.conn.execute(text("SELECT count(*) FROM runtime.graph_nodes WHERE " + RUN), self.params).scalar_one()
        ensure(count + len(intents) <= self.graph["max_activations"], "graph_activation_limit")
        inputs.validate(node.body.inputs, self.plan.document.definition.scope)
        GraphStorage.create_scope(self.conn, self.params, address, inputs, intents, row["activation_id"])

    def scatter(self, scope, row, node):
        environment = scope.environment
        if row["status"] == "ready":
            value = environment.source(node.collection)
            ensure(value.kind == "collection" and len(value.items) <= node.max_members, "graph_scatter_membership_invalid")
            ensure(all(item.kind != "missing" for item in value.items), "graph_scatter_missing_input")
            persist_node(self.conn, self.params, row, "issued", state=FrozenMembership(value).record())
            return True
        state = row["state"]
        value = CollectionValue.model_validate_json(json.dumps(state["collection"]))
        ensure(FrozenMembership(value).sha256 == state["membership_sha256"], "graph_scatter_membership_conflict")
        children = self.children(row)
        active = sum(child["status"] == "active" for child in children)
        expired = self.aggregation.expired(scope, node)
        if not expired and state["next_index"] < len(value.items) and active < node.max_parallel:
            index = state["next_index"]
            inputs = BoundValues((*environment.bind(node.captures).bindings,
                                  GraphBinding(port=node.item_input, value=value.items[index])))
            self.create(scope, row, node, index, inputs, state["membership_sha256"])
            persist_node(self.conn, self.params, row, "issued", state={**state, "next_index": index + 1})
            return True
        pending = active or state["next_index"] < len(value.items)
        if pending and not expired:
            return False
        members = []
        for child in children:
            status = "succeeded" if child["status"] == "completed" else child["status"]
            result = BoundValues.from_records(child["outputs"]).values[node.result_port] if status == "succeeded" else None
            members.append(self.aggregation.member(str(child["occurrences"][-1]["index"]), status, True, result))
        for index in range(state["next_index"], len(value.items)):
            members.append(self.aggregation.member(str(index), "pending", True, None, "member_not_started"))
        return self.aggregation.close(row, node, members, "deadline" if pending else "all_terminal")

    def iterate(self, scope, row, node):
        environment = scope.environment
        captures = environment.bind(node.captures)
        if row["status"] == "ready":
            inputs = BoundValues((*captures.bindings, *(GraphBinding(port=slot.name, value=environment.source(slot.initial))
                                                        for slot in node.state)))
            self.create(scope, row, node, 0, inputs)
            persist_node(self.conn, self.params, row, "issued", state={"iteration": 0})
            return True
        children = self.children(row)
        child = children[-1]
        if child["status"] == "active":
            return False
        ensure(child["status"] == "completed", "graph_iteration_body_unavailable")
        outputs = BoundValues.from_records(child["outputs"])
        index = child["occurrences"][-1]["index"]
        evaluator = PredicateValues(ValueEnvironment(environment.inputs, environment.outputs, outputs), self.artifacts)
        until = evaluator.evaluate(node.until)
        at_limit = index + 1 == node.max_iterations
        if until or at_limit and node.on_limit == "finish":
            persist_node(self.conn, self.params, row, "succeeded", outputs=outputs,
                         state={"iteration": index, "stop": "predicate" if until else "limit"})
            return True
        ensure(not at_limit, "graph_iteration_limit")
        inputs = BoundValues((*captures.bindings, *(GraphBinding(port=slot.name, value=outputs.values[slot.feedback_port])
                                                    for slot in node.state)))
        self.create(scope, row, node, index + 1, inputs)
        persist_node(self.conn, self.params, row, "issued", state={"iteration": index + 1})
        return True
