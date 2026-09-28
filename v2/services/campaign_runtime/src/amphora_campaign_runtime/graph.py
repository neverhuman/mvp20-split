"""Immutable structural graph values and bounded validation, independent of HTTP."""

from collections import Counter, deque
from dataclasses import dataclass

from amphora_contracts_campaigns import Branch, GraphBody, Iterate


@dataclass(frozen=True)
class Issue:
    code: str
    location: str
    message: str


@dataclass(frozen=True)
class Vertex:
    identity: str
    kind: str
    predicate_source: str | None = None
    body: "Graph | None" = None


@dataclass(frozen=True)
class Route:
    source: str
    target: str
    label: str


@dataclass(frozen=True)
class Graph:
    vertices: tuple[Vertex, ...]
    routes: tuple[Route, ...]

    @classmethod
    def from_contract(cls, body: GraphBody, depth: int = 0) -> "Graph":
        if depth > 8:
            raise ValueError("loop_nesting_limit")
        return cls(
            tuple(
                Vertex(
                    n.node_id,
                    n.kind,
                    n.predicate.source_node if isinstance(n, Branch) else None,
                    cls.from_contract(n.body, depth + 1) if isinstance(n, Iterate) else None,
                )
                for n in body.nodes
            ),
            tuple(Route(e.source, e.target, e.route) for e in body.edges),
        )

    def issues(self, location: str = "body") -> tuple[Issue, ...]:
        result: list[Issue] = []

        def add(code: str, message: str, suffix: str = "") -> None:
            result.append(Issue(code, f"{location}{suffix}", message))

        ids = [v.identity for v in self.vertices]
        if len(ids) != len(set(ids)):
            add("duplicate_node", "Node identities must be unique within one graph scope.")
            return tuple(result)
        nodes = {v.identity: v for v in self.vertices}
        incoming = {key: set() for key in nodes}
        outgoing = {key: [] for key in nodes}
        if len(self.routes) != len(set(self.routes)):
            add("duplicate_edge", "An identical route is declared more than once.")
        for edge in self.routes:
            if edge.source not in nodes or edge.target not in nodes:
                add("unknown_endpoint", "An edge endpoint is outside this graph scope.")
                continue
            incoming[edge.target].add(edge.source)
            outgoing[edge.source].append(edge)
        if result:
            return tuple(result)
        degrees = {key: len(value) for key, value in incoming.items()}
        queue = deque(key for key, count in degrees.items() if count == 0)
        visited = []
        while queue:
            key = queue.popleft()
            visited.append(key)
            for target in {e.target for e in outgoing[key]}:
                degrees[target] -= 1
                if degrees[target] == 0:
                    queue.append(target)
        if len(visited) != len(nodes):
            add("unstructured_cycle", "Cycles require a bounded iterate body; direct cycles are invalid.")
        for key, node in nodes.items():
            labels = Counter(e.label for e in outgoing[key])
            suffix = f".nodes.{key}"
            if node.kind == "branch":
                if labels != Counter({"true": 1, "false": 1}):
                    add("branch_routes", "A branch requires exactly one true and one false route.", suffix)
                ancestors: set[str] = set()
                pending = list(incoming[key])
                while pending:
                    predecessor = pending.pop()
                    if predecessor not in ancestors:
                        ancestors.add(predecessor)
                        pending.extend(incoming[predecessor])
                if node.predicate_source not in ancestors or node.predicate_source == key:
                    add(
                        "predicate_dependency",
                        "Predicate source must be a preceding node in this scope.",
                        suffix,
                    )
            elif any(e.label != "next" for e in outgoing[key]):
                add("unexpected_route", "Only branch nodes may emit true/false routes.", suffix)
            if node.kind == "finish" and outgoing[key]:
                add("terminal_successor", "Finish nodes cannot dispatch successors.", suffix)
            if node.kind != "finish" and not outgoing[key]:
                add("unterminated_path", "Nonterminal nodes require a successor.", suffix)
            if node.kind == "join" and len(incoming[key]) < 2:
                add("join_predecessors", "A join requires at least two distinct predecessors.", suffix)
            if node.body is not None:
                result.extend(node.body.issues(location + suffix + ".body"))
        if not any(n.kind == "finish" for n in self.vertices):
            add("missing_finish", "A graph scope needs an explicit finish node.")
        return tuple(result)
