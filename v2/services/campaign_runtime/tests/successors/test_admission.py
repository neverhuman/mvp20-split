"""Real transaction proof for new runs, precise carry cuts and immutable ancestry."""

import copy
from dataclasses import replace

import pytest
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.coordinator.reads import GraphReads
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.successors.reads import SuccessorReads
from amphora_contracts_core import Scope
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..compiler.conftest import definition


def setup(graph, *, finish=True):
    raw = copy.deepcopy(graph.raw)
    scalar = {"kind": "scalar", "scalar": "integer", "unit": "1"}
    raw["body"] = {"inputs": [{"name": "value", "value_type": scalar}],
        "outputs": [{"name": "value", "value_type": scalar}],
        "nodes": [{"kind": "finish", "node_id": "finish", "outputs": [
            {"port": "value", "source": {"kind": "input", "name": "value"}}]}], "edges": []}
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    service = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    payload = {"plan_sha256": entry.plan.sha256, "inputs": [{"port": "value", "value": {"kind": "integer", "value": 17}}],
        "budget": {"limit": 1}}
    original = graph.command("graph.admit", payload)
    receipt = service.admit(graph.env.principal, original)
    run = receipt.outcome.committed.object_id
    if finish:
        GraphAdvancer(graph.env.engine).advance(graph.env.principal, graph.command("graph.advance", {"run_id": run}))
    return service, payload, run, original, receipt


def proposal(graph, payload, run):
    observed = SuccessorReads(graph.env.engine).sources(graph.env.principal, run)
    source = observed.sources[0]
    return {**payload, "inputs": [], "predecessor": observed.predecessor.model_dump(mode="json"),
        "carried": [{"target_port": "value", "source": source.source.model_dump(mode="json"),
            "expected_value_sha256": source.value_sha256}]}


def test_carried_value_and_original_history_survive_new_admission(graph_env):
    graph = graph_env
    service, payload, run, original, receipt = setup(graph)
    parent = GraphReads(graph.env.engine).run(graph.env.principal, run)
    data = proposal(graph, payload, run)
    command = graph.command("graph.admit_successor", data)
    successor = service.admit_successor(graph.env.principal, command)
    assert successor.outcome.status == "accepted"
    new_run = successor.outcome.committed.object_id
    assert new_run != run
    assert service.admit_successor(graph.env.principal, command) == successor
    assert service.admit(graph.env.principal, original) == receipt
    assert GraphReads(graph.env.engine).run(graph.env.principal, run) == parent
    reads = SuccessorReads(graph.env.engine)
    lineage = reads.lineage(graph.env.principal, new_run)
    assert lineage.predecessor.run_id == run and lineage.predecessor.revision == parent.revision
    GraphAdvancer(graph.env.engine).advance(graph.env.principal, graph.command("graph.advance", {"run_id": new_run}))
    assert reads.sources(graph.env.principal, new_run).sources[0].value_sha256 == data["carried"][0]["expected_value_sha256"]
    assert reads.lineage(graph.env.principal, new_run) == lineage
    with graph.env.engine.connect() as conn, conn.begin():
        for sql in ("UPDATE runtime.graph_successors SET carried='[]'", "DELETE FROM runtime.graph_successors"):
            with pytest.raises(DBAPIError), conn.begin_nested():
                conn.execute(text(sql))


@pytest.mark.parametrize("case,reason", [
    ("revision", "predecessor_cut_changed"), ("plan", "predecessor_cut_changed"),
    ("hash", "carry_value_changed"), ("port", "carry_source_unavailable"),
    ("node", "carry_source_unavailable"), ("duplicate", "duplicate_graph_input"),
    ("overlap", "duplicate_graph_input"), ("foreign", "predecessor_unavailable"),
    ("target", "graph_input_ports_mismatch"),
])
def test_rejected_transfer_creates_no_successor(graph_env, case, reason):
    graph = graph_env
    service, payload, run, _, _ = setup(graph)
    data = proposal(graph, payload, run)
    if case == "revision":
        data["predecessor"]["revision"] += 1
    elif case == "plan":
        data["predecessor"]["plan_sha256"] = "f" * 64
    elif case == "hash":
        data["carried"][0]["expected_value_sha256"] = "0" * 64
    elif case == "port":
        data["carried"][0]["source"]["port"] = "absent"
    elif case == "node":
        data["carried"][0]["source"] = {"kind": "node_output", "activation_id": "f" * 64, "port": "value"}
    elif case == "duplicate":
        data["carried"] *= 2
    elif case == "overlap":
        data["inputs"] = payload["inputs"]
    elif case == "foreign":
        data["predecessor"]["run_id"] = "foreign"
    elif case == "target":
        data["carried"][0]["target_port"] = "other"
    command = graph.command("graph.admit_successor", data)
    denied = service.admit_successor(graph.env.principal, command)
    assert denied.outcome.reason_code == reason
    assert service.admit_successor(graph.env.principal, command) == denied
    with graph.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_successors WHERE parent_run_id=:run"), {"run": run}).scalar_one() == 0


def test_active_predecessor_rejection_is_final_after_cancellation(graph_env):
    graph = graph_env
    service, payload, run, _, _ = setup(graph, finish=False)
    data = {**payload, "predecessor": {"run_id": run, "plan_sha256": payload["plan_sha256"], "revision": 0}, "carried": []}
    command = graph.command("graph.admit_successor", data)
    denied = service.admit_successor(graph.env.principal, command)
    assert denied.outcome.reason_code == "predecessor_not_terminal"
    AuthorityCommands(graph.env.engine).cancel(graph.env.principal, graph.command("runtime.cancel", {"run_id": run, "reason_code": "test"}))
    assert service.admit_successor(graph.env.principal, command) == denied
    page = GraphReads(graph.env.engine).run(graph.env.principal, run)
    data["predecessor"]["revision"] = page.revision
    assert service.admit_successor(graph.env.principal, graph.command("graph.admit_successor", data)).outcome.status == "accepted"


def test_scoped_reads_and_atomic_ancestry_rollback(graph_env, monkeypatch):
    from amphora_campaign_runtime.successors.transfer import CarryTransfer
    graph = graph_env
    service, payload, run, _, _ = setup(graph)
    data = proposal(graph, payload, run)
    other = replace(graph.env.principal, scope=Scope(tenant_id="other", project_id="other"))
    with pytest.raises(TransitionError, match="predecessor_unavailable"):
        SuccessorReads(graph.env.engine).sources(other, run)
    original = CarryTransfer.persist

    def fail(self, *args):
        original(self, *args)
        raise RuntimeError("after_ancestry")

    monkeypatch.setattr(CarryTransfer, "persist", fail)
    command = graph.command("graph.admit_successor", data)
    with pytest.raises(RuntimeError, match="after_ancestry"):
        service.admit_successor(graph.env.principal, command)
    with graph.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_successors WHERE parent_run_id=:run"), {"run": run}).scalar_one() == 0
    monkeypatch.setattr(CarryTransfer, "persist", original)
    assert service.admit_successor(graph.env.principal, command).outcome.status == "accepted"
