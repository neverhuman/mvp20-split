"""Actual coordinator death at insert/join/checkpoint boundaries, observed through public DTOs."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_campaign_runtime.graph_inspection.details import GraphDetails
from amphora_campaign_runtime.graph_inspection.events import GraphInvalidations
from amphora_campaign_runtime.graph_inspection.snapshots import GraphSnapshots
from amphora_campaign_runtime.inspection.cursors import CursorCodec, InspectionError
from sqlalchemy import text

from ..scheduling.test_advancement import admit, advance, claim, complete, table
from ..scheduling.test_process_recovery import CoordinatorProcess


def boundary(graph, run):
    codec = CursorCodec("process-observation-stable-key-" * 2)
    return GraphSnapshots(graph.env.engine, codec), GraphDetails(graph.env.engine, codec), GraphInvalidations(graph.env.engine, codec)


def stable_pages(snapshots, graph, run):
    first = snapshots.page(graph.env.principal, run, limit=1)
    nodes, cursor = list(first.nodes), first.next_cursor
    while cursor:
        following = snapshots.page(graph.env.principal, run, limit=1, cursor=cursor)
        assert following.snapshot == first.snapshot
        nodes.extend(following.nodes)
        cursor = following.next_cursor
    assert len(nodes) == first.snapshot.node_count == len({node.activation_id for node in nodes})
    return first.snapshot.cut, nodes


def record(graph, case, before, held, after, receipt, events):
    folder = Path(__file__).absolute().parents[4] / ".test-results/graph-observation-process" / graph.env.principal.scope.project_id
    folder.mkdir(parents=True, exist_ok=True)
    evidence = {"case": case, "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "before": before.model_dump(mode="json"), "at_barrier": held.model_dump(mode="json"),
        "after_replacement": after.model_dump(mode="json"), "original_receipt": receipt.model_dump(mode="json"),
        "events": [event.model_dump(mode="json") for event in events], "real_process_killed": True,
        "replacement_replayed_original_receipt": True, "stable_page_size": 1}
    (folder / (case + ".json")).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_uncommitted_activation_is_invisible_and_replacement_reconstructs(graph_env, tmp_path):
    graph = graph_env
    run = admit(graph, 1, [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": True}}])
    snapshots, _, events = boundary(graph, run)
    before = snapshots.page(graph.env.principal, run, limit=1)
    command = graph.command("graph.advance", {"run_id": run})
    start = tmp_path / "go"
    start.write_text("go", encoding="utf-8")
    original = CoordinatorProcess(graph, tmp_path, "insert", command, start, probe=Path(__file__).with_name("activation_probe.py"))
    try:
        original.wait(".inserted")
        held, _ = stable_pages(snapshots, graph, run)
        assert held == before.snapshot.cut
        assert not table(graph, run, "activations")
        assert not events.page(graph.env.principal, run, cursor=before.snapshot.event_cursor).entries
    finally:
        original.close()
    assert stable_pages(snapshots, graph, run)[0] == before.snapshot.cut
    replacement = CoordinatorProcess(graph, tmp_path, "replace", command, start)
    try:
        receipt = replacement.reply()
        assert receipt.outcome.status == "accepted"
    finally:
        replacement.close()
    after, nodes = stable_pages(snapshots, graph, run)
    assert {node.path.node_id: node.status for node in nodes} == {
        "choose": "succeeded", "left": "issued", "right": "skipped", "collect": "waiting", "finish": "waiting"}
    assert len(table(graph, run, "activations")) == 1
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        snapshots.page(graph.env.principal, run, cursor=before.next_cursor)
    notifications = events.page(graph.env.principal, run, cursor=before.snapshot.event_cursor)
    assert [entry.revision for entry in notifications.entries] == [before.snapshot.cut.revision + 1]
    from amphora_campaign_runtime.coordinator import GraphAdvancer
    assert GraphAdvancer(graph.env.engine).advance(graph.env.principal, command) == receipt
    record(graph, "activation-uncommitted", before.snapshot.cut, held, after, receipt, notifications.entries)


@pytest.mark.parametrize("case", ["join", "iteration"])
def test_committed_cut_survives_kill_before_reply_and_reader_restart(graph_env, tmp_path, case):
    graph = graph_env
    if case == "join":
        run = admit(graph, 1, [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": True}}])
        advance(graph, run)
        complete(graph, run, claim(graph, run), "committed-left")
        for _ in range(12):
            rows = {row["node_id"]: row for row in table(graph, run, "graph_nodes")}
            if rows["collect"]["status"] == "ready":
                break
            advance(graph, run, 1)
        assert rows["collect"]["status"] == "ready"
    else:
        def modify(raw):
            loop = raw["body"]["nodes"][0]
            loop["body"]["nodes"][0]["outputs"][0]["source"] = {"kind": "integer", "value": 1, "unit": "1"}
            loop["until"]["right"]["value"] = 2
        run = admit(graph, 3, [], modify=modify)
        for _ in range(12):
            children = [row for row in table(graph, run, "graph_scopes") if row["occurrences"]]
            if children and children[0]["status"] == "completed":
                break
            advance(graph, run, 1)
        assert len(children) == 1 and children[0]["status"] == "completed"
    snapshots, details, events = boundary(graph, run)
    before = snapshots.page(graph.env.principal, run, limit=1)
    command = graph.command("graph.advance", {"run_id": run, "max_transitions": 1})
    start = tmp_path / "go"
    start.write_text("go", encoding="utf-8")
    original = CoordinatorProcess(graph, tmp_path, "committed", command, start, hold=True)
    try:
        original.wait(".committed")
        assert not original.path.with_suffix(".reply").exists()
        held, _ = stable_pages(snapshots, graph, run)
        assert held.revision == before.snapshot.cut.revision + 1
        with graph.env.engine.connect() as conn:
            original_receipt = conn.execute(text("SELECT receipt FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project "
                "AND command_id=:command"), {"tenant": graph.env.principal.scope.tenant_id, "project": graph.env.principal.scope.project_id,
                "command": command.identity.command_id}).scalar_one()
        with pytest.raises(InspectionError, match="snapshot_unavailable"):
            snapshots.page(graph.env.principal, run, cursor=before.next_cursor)
    finally:
        original.close()
    replacement = CoordinatorProcess(graph, tmp_path, "replacement", command, start)
    try:
        receipt = replacement.reply()
        assert receipt.model_dump(mode="json") == original_receipt
    finally:
        replacement.close()
    snapshots, details, events = boundary(graph, run)
    after, nodes = stable_pages(snapshots, graph, run)
    assert after == held
    fresh = snapshots.page(graph.env.principal, run)
    if case == "join":
        joined = next(node for node in nodes if node.path.node_id == "collect")
        assert joined.status == "succeeded"
        detail = details.node(graph.env.principal, run, joined.activation_id, snapshot_token=fresh.snapshot.snapshot_token)
        assert detail.outputs[0].item_count == 1 and detail.outputs[0].missing_count == 0
        values = details.values(graph.env.principal, run, joined.activation_id, detail.outputs[0].port,
            snapshot_token=fresh.snapshot.snapshot_token)
        assert values.items[0].value.artifact.artifact_id == "committed-left"
    else:
        children = sorted((row for row in table(graph, run, "graph_scopes") if row["occurrences"]), key=lambda row: row["occurrences"][0]["index"])
        assert len(children) == 2 and children[1]["inputs"] == children[0]["outputs"]
        assert children[0]["outputs"][0]["value"]["value"] == 1
        nested = [node for node in nodes if node.path.occurrences]
        assert len(nested) == 2
        for node in nested:
            detail = details.node(graph.env.principal, run, node.activation_id, snapshot_token=fresh.snapshot.snapshot_token)
            assert detail.parent_activation_id == next(node.activation_id for node in nodes if node.path.node_id == "loop")
    notifications = events.page(graph.env.principal, run, cursor=before.snapshot.event_cursor)
    assert [entry.revision for entry in notifications.entries] == [held.revision]
    record(graph, case + "-committed", before.snapshot.cut, held, after, receipt, notifications.entries)
    assert advance(graph, run).status == "completed"
