"""Independent neighborhood oracles distinguish authored edges from display order."""

import pytest
from amphora_campaign_runtime.graph_navigation.topology import ScopeTopology
from amphora_campaign_runtime.inspection.cursors import InspectionError
from amphora_contracts_graph_runtime import GraphTopologyQuery


def row(node, number):
    return {"node_id": node, "activation_id": f"{number:064x}", "kind": "finish", "status": "waiting",
            "path": {"schema_version": "2", "node_id": node, "occurrences": []}, "reason_code": None, "child_scope_count": 0}


def topology():
    rows = [row("a", 4), row("b", 1), row("c", 3), row("d", 2)]
    definition = {"nodes": [{"node_id": key, "kind": "finish"} for key in "abcd"], "edges": [
        {"source": "a", "target": "b", "route": "next"}, {"source": "a", "target": "c", "route": "next"},
        {"source": "c", "target": "d", "route": "next"}]}
    return ScopeTopology.from_authored(rows, definition)


@pytest.mark.parametrize("radius,ids,edges", [(0, [4], 0), (1, [1, 3, 4], 2), (2, [1, 2, 3, 4], 3)])
def test_neighborhood_expands_explicit_controls_both_directions(radius, ids, edges):
    result = topology().neighborhood(GraphTopologyQuery(focus_activation_id=f"{4:064x}", radius=radius))
    assert [int(node.activation_id, 16) for node in result.nodes] == ids
    assert len(result.edges) == edges


def test_pagination_emits_each_authored_edge_once_without_inventing_sorted_neighbors():
    graph = topology()
    nodes, edges, after = graph.page("", 2)
    assert [int(node.activation_id, 16) for node in nodes] == [1, 2]
    assert not edges
    remaining, edges, final = graph.page(after, 2)
    assert [int(node.activation_id, 16) for node in remaining] == [3, 4] and final is None
    assert {(int(edge.source, 16), int(edge.target, 16)) for edge in edges} == {(4, 1), (4, 3), (3, 2)}
    assert [node.to_wire().activation.path.node_id for node in remaining] == ["c", "a"]
    assert all(edge.to_wire().route == "next" for edge in edges)
    with pytest.raises(InspectionError, match="graph_node_unavailable"):
        graph.neighborhood(GraphTopologyQuery(focus_activation_id="f" * 64))


@pytest.mark.parametrize("definition", [
    {"nodes": [], "edges": []},
    {"nodes": [{"node_id": "a", "kind": "invoke"}], "edges": []},
    {"nodes": [{"node_id": "a", "kind": "finish"}], "edges": [{"source": "a", "target": "missing", "route": "next"}]},
])
def test_mismatched_retained_definition_is_not_exposed_as_valid_topology(definition):
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        ScopeTopology.from_authored([row("a", 1)], definition)
