"""Durable graph admission, immutable plan/inputs and worker lifecycle compatibility."""

import copy
from dataclasses import replace

import pytest
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.coordinator import GraphAdmission, GraphReads, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import Scope
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..compiler.conftest import definition
from ..completion.test_acceptance import Peer


def rows(env, run):
    with env.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM runtime.activations WHERE run_id=:run ORDER BY dispatch_order"),
                            {"run": run}).mappings().all()


def test_atomic_root_frontier_and_original_admission_replay(graph_env):
    graph = graph_env
    command = graph.command("graph.admit", graph.payload)
    receipt = graph.admission.admit(graph.env.principal, command)
    run = receipt.outcome.committed.object_id
    assert graph.admission.admit(graph.env.principal, command) == receipt
    page = GraphReads(graph.env.engine).run(graph.env.principal, run, limit=1)
    assert page.node_count == 2 and (page.reserved, page.spent) == (0, 0)
    second = GraphReads(graph.env.engine).run(graph.env.principal, run, after=page.next_after, limit=1)
    assert second.next_after is None
    assert {node.status for node in (*page.nodes, *second.nodes)} == {"waiting", "issued"}
    assert len(rows(graph.env, run)) == 1
    denied = graph.admission.admit(graph.env.principal, graph.command("graph.admit", graph.payload))
    assert denied.outcome.reason_code == "active_run_exists"
    other = replace(graph.env.principal, scope=Scope(tenant_id="other", project_id="other"))
    with pytest.raises(TransitionError, match="run_unavailable"):
        GraphReads(graph.env.engine).run(other, run)


@pytest.mark.parametrize("case,code", [
    ("unknown-plan", "graph_plan_unavailable"), ("duplicate-input", "duplicate_graph_input"),
    ("missing-input", "graph_input_ports_mismatch"), ("unit", "graph_input_type_mismatch"),
    ("node-limit", "graph_activation_limit"),
])
def test_rejection_receipts_create_no_run_or_frontier(graph_env, case, code):
    graph = graph_env
    payload = copy.deepcopy(graph.payload)
    if case == "unknown-plan":
        payload["plan_sha256"] = "0" * 64
    elif case == "duplicate-input":
        payload["inputs"].append(payload["inputs"][0])
    elif case == "missing-input":
        payload["inputs"] = []
    elif case == "unit":
        payload["inputs"][0]["value"]["unit"] = "g/mol"
    else:
        payload["limits"] = {"max_activations": 1}
    command = graph.command("graph.admit", payload)
    result = graph.admission.admit(graph.env.principal, command)
    assert result.outcome.reason_code == code
    assert graph.admission.admit(graph.env.principal, command) == result
    with graph.env.engine.connect() as conn:
        for table in ("runs", "graph_plans", "graph_nodes"):
            assert conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"),
                {"tenant": graph.env.principal.scope.tenant_id, "project": graph.env.principal.scope.project_id}).scalar_one() == 0


def test_frontier_failure_rolls_back_plan_run_and_notification(graph_env, monkeypatch):
    from amphora_campaign_runtime.coordinator.storage import GraphStorage
    graph = graph_env
    original = GraphStorage.create_scope

    def fail(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("after_frontier_insert")

    monkeypatch.setattr(GraphStorage, "create_scope", fail)
    command = graph.command("graph.admit", graph.payload)
    with pytest.raises(RuntimeError, match="after_frontier_insert"):
        graph.admission.admit(graph.env.principal, command)
    with graph.env.engine.connect() as conn:
        for table in ("runs", "graph_plans", "graph_nodes", "audit_events"):
            assert conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"),
                {"tenant": graph.env.principal.scope.tenant_id, "project": graph.env.principal.scope.project_id}).scalar_one() == 0
    monkeypatch.setattr(GraphStorage, "create_scope", original)
    assert graph.admission.admit(graph.env.principal, command).outcome.status == "accepted"


def test_worker_success_cannot_prematurely_close_graph(graph_env):
    graph = graph_env
    run = graph.admission.admit(graph.env.principal, graph.command("graph.admit", graph.payload)).outcome.committed.object_id
    tool = graph.entry.descriptors[0].binding.model_dump(mode="json")
    invocation = RuntimeLeases(graph.env.engine).claim(graph.env.principal, graph.command("runtime.claim", {
        "run_id": run, "worker_id": graph.env.principal.actor_id, "tool": tool, "lease_seconds": 30})).outcome.invocation
    page = GraphReads(graph.env.engine).run(graph.env.principal, run)
    assert (page.reserved, page.spent) == (1, 0)
    output = copy.deepcopy(graph.payload["inputs"][0]["value"]["artifact"])
    output.update(artifact_id="synthetic-output", schema_ref=graph.entry.descriptors[0].outputs[0].schema_ref.model_dump(mode="json"))
    command = graph.command("runtime.complete", {"run_id": run, "completion": {
        "schema_version": "1", "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id,
        "fence": invocation.fence, "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": output}]}}})
    service = CompletionCoordinator(graph.env.engine, Peer())
    receipt = service.complete(graph.env.principal, command)
    assert receipt.outcome.status == "accepted"
    assert service.complete(graph.env.principal, command) == receipt
    page = GraphReads(graph.env.engine).run(graph.env.principal, run)
    assert page.status == "running" and (page.spent, page.reserved) == (1, 0)
    assert rows(graph.env, run)[0]["status"] == "succeeded"


def test_service_role_cannot_rewrite_plan_or_graph_input_identity(graph_env):
    graph = graph_env
    run = graph.admission.admit(graph.env.principal, graph.command("graph.admit", graph.payload)).outcome.committed.object_id
    with graph.env.engine.connect() as conn, conn.begin():
        for statement in ("UPDATE runtime.graph_plans SET document='{}'", "DELETE FROM runtime.graph_plans",
                          "UPDATE runtime.graph_runs SET inputs='[]' WHERE run_id=:run",
                          "UPDATE runtime.runs SET execution_mode='fixture' WHERE run_id=:run"):
            with pytest.raises(DBAPIError), conn.begin_nested():
                conn.execute(text(statement), {"run": run})


def test_parallel_root_dispatch_uses_plan_order_and_claim_budget(graph_env):
    graph = graph_env
    raw = graph.raw
    second = copy.deepcopy(raw["body"]["nodes"][0])
    second["node_id"] = "zeta"
    raw["body"]["nodes"].append(second)
    raw["body"]["edges"].append({"source": "zeta", "target": "finish", "route": "next"})
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    admission = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    payload = {**graph.payload, "plan_sha256": entry.plan.sha256, "budget": {"limit": 1}}
    run = admission.admit(graph.env.principal, graph.command("graph.admit", payload)).outcome.committed.object_id
    initial = rows(graph.env, run)
    assert [row["specification"]["node_id"] for row in initial] == ["affine", "zeta"]
    leases = RuntimeLeases(graph.env.engine)
    value = {"run_id": run, "worker_id": graph.env.principal.actor_id, "tool": entry.descriptors[0].binding.model_dump(mode="json")}
    claim = leases.claim(graph.env.principal, graph.command("runtime.claim", value))
    assert claim.outcome.invocation.node_id == "affine"
    assert leases.claim(graph.env.principal, graph.command("runtime.claim", value)).outcome.status == "no_eligible_work"
    page = GraphReads(graph.env.engine).run(graph.env.principal, run)
    assert (page.budget_limit, page.reserved, page.spent) == (1, 1, 0)


def test_retained_plan_numeric_identity_survives_jsonb_and_successor_admission(graph_env):
    graph = graph_env
    raw = copy.deepcopy(graph.raw)
    raw["body"] = {"inputs": [], "outputs": [{"name": "value", "value_type": {"kind": "scalar", "scalar": "number", "unit": "1"}}],
                   "nodes": [{"kind": "finish", "node_id": "finish", "outputs": [{"port": "value", "source": {
                       "kind": "number", "value": 1e100, "unit": "1"}}]}], "edges": []}
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    admission = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    payload = {"plan_sha256": entry.plan.sha256, "inputs": [], "budget": {"limit": 1}}
    first = admission.admit(graph.env.principal, graph.command("graph.admit", payload)).outcome.committed.object_id
    AuthorityCommands(graph.env.engine).cancel(graph.env.principal, graph.command("runtime.cancel", {
        "run_id": first, "reason_code": "successor_fixture"}))
    second = admission.admit(graph.env.principal, graph.command("graph.admit", payload)).outcome.committed.object_id
    assert first != second
    assert GraphReads(graph.env.engine).run(graph.env.principal, first).status == "cancelled"
    assert GraphReads(graph.env.engine).run(graph.env.principal, second).plan_sha256 == entry.plan.sha256
