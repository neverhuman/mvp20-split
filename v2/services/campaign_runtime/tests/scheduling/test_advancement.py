"""Independent frontier/iteration expectations over the actual Runtime owner database."""

import copy

import pytest
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator import GraphAdmission, GraphReads, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.lifecycle.reads import RuntimeReads
from sqlalchemy import text

from ..compiler.conftest import definition
from ..completion.test_acceptance import Peer


def admit(graph, case, inputs, *, budget=8, limits=None, modify=None):
    raw = copy.deepcopy(graph.source.raw[case])
    raw["scope"] = graph.env.principal.scope.model_dump(mode="json")
    if modify:
        modify(raw)
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    payload = {"plan_sha256": entry.plan.sha256, "inputs": inputs, "budget": {"limit": budget}}
    if limits:
        payload["limits"] = limits
    receipt = GraphAdmission(graph.env.engine, PlanCatalog([entry])).admit(graph.env.principal,
                                                                          graph.command("graph.admit", payload))
    assert receipt.outcome.status == "accepted"
    return receipt.outcome.committed.object_id


def advance(graph, run, maximum=64, projections=None):
    # A fresh coordinator every pass ensures no in-memory frontier is required.
    command = graph.command("graph.advance", {"run_id": run, "max_transitions": maximum})
    service = GraphAdvancer(graph.env.engine, projections)
    receipt = service.advance(graph.env.principal, command)
    assert receipt.outcome.status == "accepted"
    assert GraphAdvancer(graph.env.engine, projections).advance(graph.env.principal, command) == receipt
    return GraphReads(graph.env.engine).run(graph.env.principal, run)


def table(graph, run, name):
    assert name in {"graph_nodes", "graph_scopes", "graph_runs", "activations"}
    with graph.env.engine.connect() as conn:
        return conn.execute(text(f"SELECT * FROM runtime.{name} WHERE run_id=:run"), {"run": run}).mappings().all()


def claim(graph, run):
    tool = graph.entry.descriptors[0].binding.model_dump(mode="json")
    response = RuntimeLeases(graph.env.engine).claim(graph.env.principal, graph.command("runtime.claim", {
        "run_id": run, "worker_id": graph.env.principal.actor_id, "tool": tool, "lease_seconds": 30}))
    assert response.outcome.status == "claimed"
    return response.outcome.invocation


def complete(graph, run, invocation, artifact_id="result"):
    output = copy.deepcopy(graph.payload["inputs"][0]["value"]["artifact"])
    output.update(artifact_id=artifact_id, schema_ref=graph.entry.descriptors[0].outputs[0].schema_ref.model_dump(mode="json"))
    command = graph.command("runtime.complete", {"run_id": run, "completion": {
        "schema_version": "1", "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id,
        "fence": invocation.fence, "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": output}]}}})
    service = CompletionCoordinator(graph.env.engine, Peer())
    receipt = service.complete(graph.env.principal, command)
    assert receipt.outcome.status == "accepted"
    return command, receipt


def test_committed_tool_output_advances_finish_and_original_receipt_survives(graph_env):
    graph = graph_env
    run = admit(graph, 0, graph.payload["inputs"])
    assert advance(graph, run).status == "running"
    invocation = claim(graph, run)
    command, receipt = complete(graph, run, invocation)
    page = advance(graph, run)
    assert page.status == "completed" and {node.status for node in page.nodes} == {"succeeded"}
    assert (page.spent, page.reserved) == (1, 0)
    assert RuntimeReads(graph.env.engine).run(graph.env.principal, run).activations == ()
    assert CompletionCoordinator(graph.env.engine, Peer()).complete(graph.env.principal, command) == receipt
    outputs = table(graph, run, "graph_runs")[0]["outputs"]
    assert outputs[0]["value"]["artifact"]["artifact_id"] == "result"


@pytest.mark.parametrize("flag,selected,skipped", [(True, "left", "right"), (False, "right", "left")])
def test_branch_records_route_and_join_excludes_unselected_member(graph_env, flag, selected, skipped):
    graph = graph_env
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": flag}}]
    run = admit(graph, 1, inputs)
    assert advance(graph, run).status == "running"
    rows = {row["node_id"]: row for row in table(graph, run, "graph_nodes")}
    assert rows["choose"]["state"] == {"route": "true" if flag else "false"}
    assert rows[selected]["status"] == "issued" and rows[skipped]["status"] == "skipped"
    invocation = claim(graph, run)
    assert invocation.node_id == selected
    complete(graph, run, invocation, selected)
    assert advance(graph, run).status == "completed"
    results = table(graph, run, "graph_runs")[0]["outputs"][0]["value"]["items"]
    assert [value["artifact"]["artifact_id"] for value in results] == [selected]


@pytest.mark.parametrize("on_limit,expected", [("finish", "completed"), ("blocked", "blocked")])
def test_loop_reloads_checkpoints_and_stops_at_declared_limit(graph_env, on_limit, expected):
    graph = graph_env
    run = admit(graph, 3, [], modify=lambda raw: raw["body"]["nodes"][0].update(on_limit=on_limit))
    for _ in range(15):
        page = advance(graph, run, 1)
        if page.status != "running":
            break
    assert page.status == expected
    children = sorted((row for row in table(graph, run, "graph_scopes") if row["occurrences"]),
                      key=lambda row: row["occurrences"][0]["index"])
    assert [row["occurrences"] for row in children] == [
        [{"kind": "loop", "node_id": "loop", "index": 0}], [{"kind": "loop", "node_id": "loop", "index": 1}]]
    assert all(row["status"] == "completed" for row in children)
    assert children[1]["inputs"] == children[0]["outputs"]
    assert (page.spent, page.reserved) == (0, 0)


def test_zero_scatter_has_empty_result_and_no_child_or_tool(graph_env):
    graph = graph_env
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": []}}])
    page = advance(graph, run)
    assert page.status == "completed" and page.node_count == 2
    assert table(graph, run, "activations") == []
    assert table(graph, run, "graph_runs")[0]["outputs"] == [{"port": "results", "value": {"kind": "collection", "items": []}}]


def test_scatter_freezes_order_refills_capacity_and_ignores_completion_order(graph_env):
    graph = graph_env
    items = []
    for index in range(3):
        value = copy.deepcopy(graph.payload["inputs"][0]["value"])
        value["artifact"]["artifact_id"] = "input-" + str(index)
        items.append(value)
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": items}}])
    advance(graph, run)
    assert len(table(graph, run, "activations")) == 2
    first, second = claim(graph, run), claim(graph, run)
    assert [work.inputs[0].artifact.artifact_id for work in (first, second)] == ["input-0", "input-1"]
    complete(graph, run, second, "output-1")
    advance(graph, run)
    third = claim(graph, run)
    assert third.inputs[0].artifact.artifact_id == "input-2"
    complete(graph, run, third, "output-2")
    assert advance(graph, run).status == "running"
    complete(graph, run, first, "output-0")
    assert advance(graph, run).status == "completed"
    outputs = table(graph, run, "graph_runs")[0]["outputs"][0]["value"]["items"]
    assert [value["artifact"]["artifact_id"] for value in outputs] == ["output-0", "output-1", "output-2"]
    children = [row for row in table(graph, run, "graph_scopes") if row["occurrences"]]
    assert len({row["occurrences"][0]["membership_sha256"] for row in children}) == 1


def test_expansion_bound_blocks_without_partial_child_insert(graph_env):
    graph = graph_env
    run = admit(graph, 3, [], limits={"max_activations": 3})
    page = advance(graph, run)
    assert page.status == "blocked" and page.node_count == 3
    assert len(table(graph, run, "graph_scopes")) == 2
    loop = next(row for row in table(graph, run, "graph_nodes") if row["node_id"] == "loop")
    assert loop["reason_code"] == "graph_activation_limit"


def test_exhausted_budget_is_settled_and_dependency_blocks(graph_env):
    graph = graph_env
    items = [graph.payload["inputs"][0]["value"]] * 2
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": items}}], budget=1)
    advance(graph, run)
    complete(graph, run, claim(graph, run))
    page = advance(graph, run)
    assert page.status == "blocked" and (page.spent, page.reserved) == (1, 0)
    assert {row["status"] for row in table(graph, run, "activations")} == {"succeeded", "failed"}
    assert not {node.status for node in page.nodes} & {"ready", "waiting", "issued"}


def test_graph_deadline_settles_issued_work_once(graph_env):
    import time
    graph = graph_env
    run = admit(graph, 0, graph.payload["inputs"], limits={"deadline_seconds": 1})
    claim(graph, run)
    time.sleep(1.05)
    page = advance(graph, run)
    assert page.status == "blocked" and page.stop_reason == "graph_deadline_exhausted"
    assert (page.spent, page.reserved) == (1, 0)
    assert {node.status for node in page.nodes} == {"blocked"}


def test_active_worker_window_preserves_all_leases_beyond_256_history_rows(graph_env):
    graph = graph_env

    def enlarge(raw):
        body = raw["body"]
        body["inputs"][0]["value_type"]["max_items"] = 257
        body["outputs"][0]["value_type"]["max_items"] = 257
        body["nodes"][0].update(max_members=257, max_parallel=257)
        body["nodes"][0]["output"]["value_type"]["max_items"] = 257

    items = [graph.payload["inputs"][0]["value"]] * 257
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": items}}], modify=enlarge, budget=300)
    for _ in range(3):
        advance(graph, run, 256)
    rows = table(graph, run, "activations")
    assert len(rows) == 256 and {row["status"] for row in rows} == {"queued"}
    first = claim(graph, run)
    complete(graph, run, first)
    advance(graph, run, 256)
    assert len(table(graph, run, "activations")) == 257
    snapshot = RuntimeReads(graph.env.engine).run(graph.env.principal, run)
    assert len(snapshot.activations) == 256
    assert first.activation_id not in {value.activation_id for value in snapshot.activations}
    next_work = claim(graph, run)
    snapshot = RuntimeReads(graph.env.engine).run(graph.env.principal, run)
    assert next_work.attempt_id in {value.latest_attempt.attempt_id for value in snapshot.activations if value.latest_attempt}


def test_advance_rollback_preserves_original_frontier_and_pending_command(graph_env, monkeypatch):
    graph = graph_env
    run = admit(graph, 3, [])
    command = graph.command("graph.advance", {"run_id": run})
    service = GraphAdvancer(graph.env.engine)
    original = service.leases._changed

    def interrupted(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("before_commit")

    monkeypatch.setattr(service.leases, "_changed", interrupted)
    with pytest.raises(RuntimeError, match="before_commit"):
        service.advance(graph.env.principal, command)
    assert len(table(graph, run, "graph_scopes")) == 1
    assert len(table(graph, run, "graph_nodes")) == 2
    assert table(graph, run, "graph_runs")[0]["frontier_revision"] == 0
    monkeypatch.setattr(service.leases, "_changed", original)
    receipt = service.advance(graph.env.principal, command)
    assert receipt.outcome.status == "accepted"
    assert service.advance(graph.env.principal, command) == receipt
    assert GraphReads(graph.env.engine).run(graph.env.principal, run).status == "completed"
