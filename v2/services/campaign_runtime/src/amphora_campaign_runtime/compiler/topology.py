"""Deterministic scoped DAG order and control-dependent value availability."""

import heapq
from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType

from .errors import require


@dataclass(frozen=True)
class NodeFlow:
    conditions: tuple
    guaranteed: frozenset


class ScopeTopology:
    def __init__(self, body, location):
        nodes = {node.node_id: node for node in body.nodes}
        require(len(nodes) == len(body.nodes), "duplicate_node", location)
        incoming, outgoing = {key: [] for key in nodes}, {key: [] for key in nodes}
        edges = [(edge.source, edge.target, edge.route) for edge in body.edges]
        require(len(set(edges)) == len(edges), "duplicate_edge", location)
        for edge in body.edges:
            require(edge.source in nodes and edge.target in nodes, "unknown_endpoint", location)
            outgoing[edge.source].append(edge)
            incoming[edge.target].append(edge)
        require(sum(node.kind == "finish" for node in body.nodes) == 1, "single_scope_finish_required", location)
        for key, node in nodes.items():
            routes = Counter(edge.route for edge in outgoing[key])
            if node.kind == "branch":
                require(routes == Counter({"true": 1, "false": 1}), "branch_routes", location + "." + key)
            else:
                require(all(edge.route == "next" for edge in outgoing[key]), "unexpected_route", location + "." + key)
            require(not outgoing[key] if node.kind == "finish" else bool(outgoing[key]),
                    "terminal_successor" if node.kind == "finish" else "unterminated_path", location + "." + key)
        degrees = {key: len({edge.source for edge in edges}) for key, edges in incoming.items()}
        ready = sorted(key for key, degree in degrees.items() if degree == 0)
        order = []
        while ready:
            key = heapq.heappop(ready)
            order.append(key)
            for target in sorted({edge.target for edge in outgoing[key]}):
                degrees[target] -= 1
                if degrees[target] == 0:
                    heapq.heappush(ready, target)
        require(len(order) == len(nodes), "unstructured_cycle", location)
        flows = {}
        for key in order:
            node, paths = nodes[key], []
            for edge in incoming[key]:
                before = flows[edge.source]
                conditions = dict(before.conditions)
                if nodes[edge.source].kind == "branch":
                    conditions[edge.source] = edge.route
                paths.append((conditions, before.guaranteed | {edge.source}))
            if not paths:
                conditions, guaranteed = {}, frozenset()
            elif node.kind == "join":
                conditions = {branch: route for branch, route in paths[0][0].items()
                              if all(path.get(branch) == route for path, _ in paths)}
                guaranteed = frozenset.intersection(*(frozenset(values) for _, values in paths))
                required = {member.source.node_id for member in node.members
                            if member.required and member.source.kind == "output"}
                if node.policy.kind == "all":
                    for edge, (condition, values) in zip(incoming[key], paths, strict=True):
                        if condition == conditions and edge.source in required:
                            guaranteed |= values
            else:
                conditions, guaranteed = {}, frozenset()
                for condition, values in paths:
                    for branch, route in condition.items():
                        require(branch not in conditions or conditions[branch] == route,
                                "implicit_branch_join", location + "." + key)
                        conditions[branch] = route
                    guaranteed |= values
            flows[key] = NodeFlow(tuple(sorted(conditions.items())), frozenset(guaranteed))
        self.nodes, self.flows = MappingProxyType(nodes), MappingProxyType(flows)
        self.order = tuple(order)
        self.incoming = MappingProxyType({key: tuple(value) for key, value in incoming.items()})

    def ancestors(self, key):
        result, pending = set(), [edge.source for edge in self.incoming[key]]
        while pending:
            node = pending.pop()
            if node not in result:
                result.add(node)
                pending.extend(edge.source for edge in self.incoming[node])
        return frozenset(result)
