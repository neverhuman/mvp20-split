"""Real elapsed owner clocks; no rewriting admission identity to manufacture expiry."""

import time
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator.state import ScopeState
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..completion.test_acceptance import Peer
from ..scheduling.test_advancement import admit, advance, claim, complete, table
from .test_execution import evidence, partial


def deadline(raw, minimum=0, seconds=2):
    partial(raw, minimum)
    node = next(node for node in raw["body"]["nodes"] if node["kind"] in {"join", "scatter"})
    node["policy"].update(close="deadline", deadline_seconds=seconds)


def wait_for_deadline(graph, run, seconds=2):
    until = time.monotonic() + seconds + 3
    while time.monotonic() < until:
        with graph.env.engine.connect() as conn:
            expired = conn.execute(text("SELECT clock_timestamp() >= opened_at + :seconds * interval '1 second' "
                "FROM runtime.graph_scopes WHERE run_id=:run AND parent_activation_id IS NULL"),
                {"run": run, "seconds": seconds}).scalar_one()
        if expired:
            return
        time.sleep(0.025)
    pytest.fail("Owned PostgreSQL clock did not reach the declared deadline")


def test_deadline_scatter_closes_unstarted_slots_without_materializing_work(graph_env):
    graph = graph_env
    item = graph.payload["inputs"][0]["value"]
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": [item, item]}}], modify=deadline)
    wait_for_deadline(graph, run)
    page = advance(graph, run)
    assert page.status == "completed" and (page.spent, page.reserved) == (0, 0)
    stored = evidence(graph, run)[0]
    assert stored["cut"]["trigger"] == "deadline"
    assert stored["decision"]["collection"]["items"] == [
        {"kind": "missing", "member_id": "0", "reason_code": "member_not_started"},
        {"kind": "missing", "member_id": "1", "reason_code": "member_not_started"}]
    assert table(graph, run, "activations") == []


def test_deadline_finish_settles_leases_and_late_report_cannot_rewrite_cut(graph_env):
    graph = graph_env
    def parallel(raw):
        deadline(raw, 1, 3)
        raw["body"]["nodes"] = [node for node in raw["body"]["nodes"] if node["node_id"] != "choose"]
        raw["body"]["edges"] = [edge for edge in raw["body"]["edges"] if edge["source"] != "choose"]
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": True}}]
    run = admit(graph, 1, inputs, modify=parallel)
    first, second = claim(graph, run), claim(graph, run)
    complete(graph, run, first, "accepted-first")
    assert advance(graph, run).status == "running"
    assert evidence(graph, run) == []
    wait_for_deadline(graph, run, 3)
    page = advance(graph, run)
    assert page.status == "completed" and (page.spent, page.reserved) == (2, 0)
    before = evidence(graph, run)
    assert [member["status"] for member in before[0]["cut"]["members"]] == ["succeeded", "pending"]
    late = graph.command("runtime.complete", {"run_id": run, "completion": {"schema_version": "1",
        "invocation_id": second.invocation_id, "attempt_id": second.attempt_id, "fence": second.fence,
        "outcome": {"status": "abstained", "reason_code": "late"}}})
    reply = CompletionCoordinator(graph.env.engine, Peer()).complete(graph.env.principal, late)
    assert reply.outcome.status == "rejected"
    assert evidence(graph, run) == before
    assert {row["status"] for row in table(graph, run, "activations")} == {"succeeded", "cancelled"}


def test_scope_clock_cannot_be_reset_by_service_role(graph_env):
    graph = graph_env
    run = admit(graph, 2, [{"port": "items", "value": {"kind": "collection", "items": []}}], modify=deadline)
    with pytest.raises(DBAPIError):
        with graph.env.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.graph_scopes SET opened_at=clock_timestamp() WHERE run_id=:run"), {"run": run})


def test_deadline_never_selects_an_unresolved_branch():
    edges = tuple(SimpleNamespace(source=source, target=target, route=route) for source, target, route in [
        ("choose", "left", "true"), ("choose", "right", "false"),
        ("left", "join", "next"), ("right", "join", "next")])
    nodes = {"choose": {"kind": "branch", "status": "ready", "state": {}},
             "left": {"kind": "invoke", "status": "waiting"},
             "right": {"kind": "invoke", "status": "waiting"}}
    state = ScopeState(None, None, nodes, None, SimpleNamespace(edges=edges))
    members = tuple(SimpleNamespace(source=SimpleNamespace(kind="output", node_id=key)) for key in ("left", "right"))
    join = SimpleNamespace(kind="join", node_id="join", members=members)
    assert state.readiness(join, deadline=True) == "waiting"
    nodes["choose"].update(status="succeeded", state={"route": "false"})
    nodes["left"]["status"] = "skipped"
    nodes["right"]["status"] = "issued"
    assert state.readiness(join, deadline=True) == "ready"
    assert state.readiness(join) == "waiting"


def test_deadline_cannot_bypass_an_unrelated_control_prerequisite():
    edges = tuple(SimpleNamespace(source=key, target="join", route="next") for key in ("member", "prerequisite"))
    nodes = {key: {"kind": "invoke", "status": "issued"} for key in ("member", "prerequisite")}
    state = ScopeState(None, None, nodes, None, SimpleNamespace(edges=edges))
    join = SimpleNamespace(kind="join", node_id="join", members=(
        SimpleNamespace(source=SimpleNamespace(kind="output", node_id="member")),))
    assert state.readiness(join, deadline=True) == "waiting"
    nodes["prerequisite"]["status"] = "succeeded"
    assert state.readiness(join, deadline=True) == "ready"


def test_expired_join_preserves_excluded_branch_and_pending_selected_member(graph_env):
    graph = graph_env
    inputs = [*graph.payload["inputs"], {"port": "flag", "value": {"kind": "boolean", "value": False}}]
    run = admit(graph, 1, inputs, modify=deadline)
    wait_for_deadline(graph, run)
    page = advance(graph, run)
    assert page.status == "completed" and (page.spent, page.reserved) == (0, 0)
    stored = evidence(graph, run)[0]
    assert [member["status"] for member in stored["cut"]["members"]] == ["skipped", "pending"]
    assert stored["decision"]["eligible_members"] == []
    assert len(stored["decision"]["collection"]["items"]) == 2
