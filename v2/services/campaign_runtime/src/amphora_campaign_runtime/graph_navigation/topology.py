"""Pure authored-control neighborhood and pagination policy, independent of SQL/HTTP."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphControlLink, GraphTopologyNode

from ..graph_inspection.policy import node_view, require


@dataclass(frozen=True)
class TopologyNode:
    row: object
    child_scope_count: int

    @property
    def activation_id(self):
        return self.row["activation_id"]

    def to_wire(self):
        return GraphTopologyNode(activation=node_view(self.row), child_scope_count=self.child_scope_count)


@dataclass(frozen=True)
class ControlLink:
    source: str
    target: str
    route: str

    def to_wire(self):
        return GraphControlLink(source=self.source, target=self.target, route=self.route)


@dataclass(frozen=True)
class ScopeTopology:
    nodes: tuple
    edges: tuple

    @classmethod
    def from_authored(cls, rows, definition):
        declared = {node["node_id"]: node["kind"] for node in definition["nodes"]}
        actual = {row["node_id"]: row for row in rows}
        require(len(declared) == len(definition["nodes"]) == len(actual) == len(rows))
        require(declared == {key: row["kind"] for key, row in actual.items()})
        nodes = tuple(TopologyNode(row, row["child_scope_count"]) for row in rows)
        edges = []
        for edge in definition["edges"]:
            require(edge["source"] in actual and edge["target"] in actual)
            require(edge["route"] in {"next", "true", "false"})
            edges.append(ControlLink(actual[edge["source"]]["activation_id"], actual[edge["target"]]["activation_id"], edge["route"]))
        require(len(set(edges)) == len(edges))
        return cls(tuple(sorted(nodes, key=lambda node: node.activation_id)), tuple(sorted(edges, key=lambda edge: (edge.source, edge.target, edge.route))))

    def neighborhood(self, query):
        if query.focus_activation_id is None:
            return self
        require(query.focus_activation_id in {node.activation_id for node in self.nodes}, "graph_node_unavailable")
        visited = {query.focus_activation_id}
        frontier = set(visited)
        for _ in range(query.radius):
            neighbors = {edge.target for edge in self.edges if edge.source in frontier} | {edge.source for edge in self.edges if edge.target in frontier}
            frontier = neighbors - visited
            visited |= frontier
        return ScopeTopology(tuple(node for node in self.nodes if node.activation_id in visited),
                             tuple(edge for edge in self.edges if edge.source in visited and edge.target in visited))

    def page(self, after, limit):
        remaining = [node for node in self.nodes if node.activation_id > after]
        nodes = tuple(remaining[:limit])
        sources = {node.activation_id for node in nodes}
        # An edge is emitted with its source page exactly once; its target may be unexpanded.
        edges = tuple(edge for edge in self.edges if edge.source in sources)
        return nodes, edges, nodes[-1].activation_id if len(remaining) > limit else None
