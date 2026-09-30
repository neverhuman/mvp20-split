"""Real PostgreSQL scope/topology reads retain authorization and snapshot boundaries."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.graph_navigation.reads import GraphNavigation
from amphora_campaign_runtime.inspection.cursors import InspectionError
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import GraphTopologyQuery

from ..graph_inspection.test_snapshots import start
from ..scheduling.test_advancement import admit, advance, claim


def test_root_scope_and_authored_link_are_not_inferred_from_activation_order(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    snapshot = snapshots.page(graph.env.principal, run)
    navigation = GraphNavigation(graph.env.engine, cursors)
    scopes = navigation.scopes(graph.env.principal, run, snapshot_token=snapshot.snapshot.snapshot_token)
    assert scopes.scope_count == 1 and scopes.scopes[0].definition_path == ()
    assert scopes.scopes[0].node_count == 2 and scopes.scopes[0].occurrences == ()
    first = navigation.topology(graph.env.principal, run, scopes.scopes[0].scope_key, snapshot_token=snapshot.snapshot.snapshot_token, limit=1)
    second = navigation.topology(graph.env.principal, run, scopes.scopes[0].scope_key, snapshot_token=snapshot.snapshot.snapshot_token, limit=1, cursor=first.next_cursor)
    names = {node.activation.activation_id: node.activation.path.node_id for node in (*first.nodes, *second.nodes)}
    assert first.cut == second.cut == snapshot.snapshot.cut and second.next_cursor is None
    assert {(names[edge.source], names[edge.target], edge.route) for edge in (*first.edges, *second.edges)} == {
        (edge["source"], edge["target"], edge.get("route", "next")) for edge in graph.raw["body"]["edges"]}
    assert first.node_count == 2 and first.edge_count == 1
    isolated = navigation.topology(graph.env.principal, run, scopes.scopes[0].scope_key,
        snapshot_token=snapshot.snapshot.snapshot_token, query=GraphTopologyQuery(focus_activation_id=first.nodes[0].activation.activation_id, radius=0))
    assert isolated.node_count == 1 and isolated.edge_count == 0
    with pytest.raises(InspectionError, match="cursor_mismatch"):
        navigation.topology(graph.env.principal, run, scopes.scopes[0].scope_key, snapshot_token=snapshot.snapshot.snapshot_token,
            cursor=first.next_cursor, query=GraphTopologyQuery(radius=2))


def test_navigation_rechecks_scope_revision_expiry_and_resource(graph_env):
    graph = graph_env
    clock = [1000]
    run, cursors, snapshots = start(graph, clock)
    token = snapshots.page(graph.env.principal, run).snapshot.snapshot_token
    navigation = GraphNavigation(graph.env.engine, cursors)
    with pytest.raises(InspectionError, match="run_unavailable"):
        navigation.scopes(replace(graph.env.principal, scope=Scope(tenant_id="other", project_id="other")), run, snapshot_token=token)
    with pytest.raises(InspectionError, match="graph_node_unavailable"):
        navigation.scopes(graph.env.principal, run, snapshot_token=token, parent_activation_id="f" * 64)
    with pytest.raises(InspectionError, match="graph_scope_unavailable"):
        navigation.topology(graph.env.principal, run, "f" * 64, snapshot_token=token)
    clock[0] += 61
    with pytest.raises(InspectionError, match="cursor_expired"):
        navigation.scopes(graph.env.principal, run, snapshot_token=token)
    fresh = snapshots.page(graph.env.principal, run).snapshot.snapshot_token
    claim(graph, run)
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        navigation.scopes(graph.env.principal, run, snapshot_token=fresh)


def test_scatter_occurrences_have_distinct_owner_scopes_and_real_child_edges(graph_env):
    graph = graph_env
    value = graph.payload["inputs"][0]["value"]
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": [value, value]}}])
    advance(graph, run)
    from amphora_campaign_runtime.graph_inspection.snapshots import GraphSnapshots
    from amphora_campaign_runtime.inspection.cursors import CursorCodec
    cursors = CursorCodec("nested-navigation-test-" * 3)
    snapshot = GraphSnapshots(graph.env.engine, cursors).page(graph.env.principal, run)
    navigation = GraphNavigation(graph.env.engine, cursors)
    group = next(node for node in snapshot.nodes if node.kind == "scatter")
    token = snapshot.snapshot.snapshot_token
    first = navigation.scopes(graph.env.principal, run, snapshot_token=token, parent_activation_id=group.activation_id, limit=1)
    second = navigation.scopes(graph.env.principal, run, snapshot_token=token, parent_activation_id=group.activation_id, limit=1, cursor=first.next_cursor)
    scopes = (*first.scopes, *second.scopes)
    assert first.scope_count == 2 and second.next_cursor is None
    assert {scope.occurrences[-1].index for scope in scopes} == {0, 1}
    activations = []
    for scope in scopes:
        assert scope.definition_path == (group.path.node_id,) and scope.parent_activation_id == group.activation_id
        page = navigation.topology(graph.env.principal, run, scope.scope_key, snapshot_token=token)
        assert page.node_count == 2 and page.edge_count == 1
        assert all(node.activation.path.occurrences == scope.occurrences for node in page.nodes)
        members = {node.activation.activation_id for node in page.nodes}
        assert all(edge.source in members and edge.target in members for edge in page.edges)
        activations.append(members)
    assert activations[0].isdisjoint(activations[1])
