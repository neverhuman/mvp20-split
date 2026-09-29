"""Actual PostgreSQL snapshot consistency, bounded lineage and durable invalidations."""

import copy
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.graph_inspection.details import GraphDetails
from amphora_campaign_runtime.graph_inspection.events import GraphInvalidations
from amphora_campaign_runtime.graph_inspection.snapshots import GraphSnapshots
from amphora_campaign_runtime.inspection.cursors import CursorCodec, InspectionError
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import GraphReadQuery
from sqlalchemy import text

from ..compiler.conftest import definition
from ..scheduling.test_advancement import advance, claim, complete


def start(graph, clock=None):
    cursors = CursorCodec("test-observation-key-" * 3, **({"clock": lambda: clock[0], "ttl_seconds": 60} if clock else {}))
    run = graph.admission.admit(graph.env.principal, graph.command("graph.admit", graph.payload)).outcome.committed.object_id
    return run, cursors, GraphSnapshots(graph.env.engine, cursors)


def test_pages_are_one_revision_and_old_page_rejects_after_claim(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    first = snapshots.page(graph.env.principal, run, limit=1)
    second = snapshots.page(graph.env.principal, run, limit=1, cursor=first.next_cursor)
    assert first.snapshot == second.snapshot
    assert second.next_cursor is None and first.nodes[0].activation_id != second.nodes[0].activation_id
    invocation = claim(graph, run)
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        snapshots.page(graph.env.principal, run, cursor=first.next_cursor)
    fresh = snapshots.page(graph.env.principal, run)
    assert fresh.snapshot.cut.revision > first.snapshot.cut.revision
    detail = GraphDetails(graph.env.engine, cursors).node(graph.env.principal, run, invocation.activation_id,
        snapshot_token=fresh.snapshot.snapshot_token)
    assert len(detail.attempts) == 1 and detail.attempts[0].status == "leased"
    assert detail.attempts[0].completion_id is None and not detail.attempts[0].canonical_result
    filtered = snapshots.page(graph.env.principal, run, query=GraphReadQuery(scope_key=detail.scope_key, frontier_only=True))
    assert len(filtered.nodes) == 2


def test_completion_lineage_output_and_contiguous_reconnect(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    initial = snapshots.page(graph.env.principal, run)
    invocation = claim(graph, run)
    complete(graph, run, invocation)
    advance(graph, run)
    page = snapshots.page(graph.env.principal, run)
    assert page.snapshot.status == "completed"
    details = GraphDetails(graph.env.engine, cursors)
    detail = details.node(graph.env.principal, run, invocation.activation_id, snapshot_token=page.snapshot.snapshot_token)
    assert detail.attempts[0].canonical_result and detail.attempts[0].completion_id
    assert detail.attempts[0].settled and detail.attempts[0].status == "succeeded"
    assert detail.outputs[0].kind == "artifact" and detail.outputs[0].item_count == 1
    output = details.values(graph.env.principal, run, invocation.activation_id, "result", snapshot_token=page.snapshot.snapshot_token)
    assert output.items[0].value.artifact == detail.outputs[0].artifact
    events = GraphInvalidations(graph.env.engine, cursors)
    cursor, revisions = initial.snapshot.event_cursor, []
    while True:
        result = events.page(graph.env.principal, run, cursor=cursor, limit=1)
        duplicate = events.page(graph.env.principal, run, cursor=cursor, limit=1)
        assert duplicate.entries == result.entries
        revisions.extend(entry.revision for entry in result.entries)
        cursor = result.next_cursor
        if not result.has_more:
            break
    assert revisions == list(range(1, page.snapshot.cut.revision + 1))
    assert not events.page(graph.env.principal, run, cursor=cursor).entries
    assert not snapshots.page(graph.env.principal, run, query=GraphReadQuery(frontier_only=True)).nodes


def test_expiry_scope_filter_and_mode_are_fail_closed(graph_env):
    graph = graph_env
    clock = [1000]
    run, cursors, snapshots = start(graph, clock)
    page = snapshots.page(graph.env.principal, run, limit=1)
    with pytest.raises(InspectionError, match="cursor_mismatch"):
        snapshots.page(graph.env.principal, run, cursor=page.next_cursor, query=GraphReadQuery(frontier_only=True))
    with pytest.raises(InspectionError, match="cursor_mismatch"):
        snapshots.page(graph.env.principal, run, cursor=page.snapshot.event_cursor)
    with pytest.raises(InspectionError, match="invalid_cursor"):
        snapshots.page(graph.env.principal, run, cursor=page.next_cursor + "x")
    foreign = replace(graph.env.principal, scope=Scope(tenant_id="foreign", project_id="foreign"))
    with pytest.raises(InspectionError, match="run_unavailable"):
        snapshots.page(foreign, run, cursor=page.next_cursor)
    with pytest.raises(InspectionError, match="graph_scope_unavailable"):
        snapshots.page(graph.env.principal, run, query=GraphReadQuery(scope_key="f" * 64))
    clock[0] += 61
    with pytest.raises(InspectionError, match="cursor_expired"):
        snapshots.page(graph.env.principal, run, cursor=page.next_cursor)
    with pytest.raises(InspectionError, match="cursor_expired"):
        GraphInvalidations(graph.env.engine, cursors).page(graph.env.principal, run, cursor=page.snapshot.event_cursor)


def test_missing_durable_revision_cannot_be_an_empty_success(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    page = snapshots.page(graph.env.principal, run)
    # Deliberate invalid owner-state cut, not an allowed production transition.
    with graph.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET revision=revision+1 WHERE run_id=:run"), {"run": run})
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        GraphInvalidations(graph.env.engine, cursors).page(graph.env.principal, run, cursor=page.snapshot.event_cursor)


def test_detail_rejects_missing_node_stale_cut_and_malformed_owner_values(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    page = snapshots.page(graph.env.principal, run)
    details = GraphDetails(graph.env.engine, cursors)
    with pytest.raises(InspectionError, match="graph_node_unavailable"):
        details.node(graph.env.principal, run, "f" * 64, snapshot_token=page.snapshot.snapshot_token)
    invocation = claim(graph, run)
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        details.node(graph.env.principal, run, invocation.activation_id, snapshot_token=page.snapshot.snapshot_token)
    fresh = snapshots.page(graph.env.principal, run)
    # Corruption injection is owner-test-only; no normal transition writes these values.
    with graph.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.graph_nodes SET outputs='[{\"port\":\"broken\"}]'::jsonb "
            "WHERE run_id=:run AND activation_id=:activation"), {"run": run, "activation": invocation.activation_id})
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        details.node(graph.env.principal, run, invocation.activation_id, snapshot_token=fresh.snapshot.snapshot_token)


def test_collection_values_are_bounded_pages_with_explicit_missing_slots(graph_env):
    graph = graph_env
    raw = copy.deepcopy(graph.raw)
    shape = {"kind": "collection", "item": {"kind": "scalar", "scalar": "integer", "unit": "1"}, "max_items": 8, "missing_slots": True}
    raw["body"] = {"inputs": [{"name": "values", "value_type": shape}], "outputs": [{"name": "values", "value_type": shape}],
        "nodes": [{"kind": "finish", "node_id": "finish", "outputs": [{"port": "values", "source": {"kind": "input", "name": "values"}}]}], "edges": []}
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    service = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    value = {"kind": "collection", "items": [{"kind": "integer", "value": 17, "unit": "1"},
        {"kind": "missing", "member_id": "candidate-1", "reason_code": "failed"}, {"kind": "integer", "value": 19, "unit": "1"}]}
    run = service.admit(graph.env.principal, graph.command("graph.admit", {"plan_sha256": entry.plan.sha256,
        "inputs": [{"port": "values", "value": value}], "budget": {"limit": 1}})).outcome.committed.object_id
    advance(graph, run)
    cursors = CursorCodec("collection-observation-test-key-" * 2)
    page = GraphSnapshots(graph.env.engine, cursors).page(graph.env.principal, run)
    details = GraphDetails(graph.env.engine, cursors)
    activation = page.nodes[0].activation_id
    detail = details.node(graph.env.principal, run, activation, snapshot_token=page.snapshot.snapshot_token)
    assert (detail.outputs[0].item_count, detail.outputs[0].missing_count, detail.outputs[0].artifact) == (3, 1, None)
    cursor, items = None, []
    for _ in range(3):
        result = details.values(graph.env.principal, run, activation, "values", snapshot_token=page.snapshot.snapshot_token, cursor=cursor, limit=1)
        items.extend(json.loads(item.value.model_dump_json()) for item in result.items)
        cursor = result.next_cursor
    assert cursor is None and items == value["items"]
