"""Lifecycle reconciliation, typed destination compatibility and public HTTP boundary."""

import copy

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.coordinator import GraphAdmission, PlanCatalog, ReviewedPlan
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.successors.reads import SuccessorReads
from fastapi.testclient import TestClient
from sqlalchemy import text

from ..compiler.conftest import definition
from ..scheduling.test_advancement import advance, claim, complete
from .test_admission import proposal, setup


def test_destination_type_rejects_valid_source_without_changing_parent(graph_env):
    graph = graph_env
    _, payload, run, _, _ = setup(graph)
    data = proposal(graph, payload, run)
    raw = copy.deepcopy(graph.raw)
    scalar = {"kind": "scalar", "scalar": "string", "unit": "1"}
    raw["body"] = {"inputs": [{"name": "value", "value_type": scalar}], "outputs": [{"name": "value", "value_type": scalar}],
        "nodes": [{"kind": "finish", "node_id": "finish", "outputs": [{"port": "value", "source": {"kind": "input", "name": "value"}}]}], "edges": []}
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    service = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    data["plan_sha256"] = entry.plan.sha256
    assert service.admit_successor(graph.env.principal, graph.command("graph.admit_successor", data)).outcome.reason_code == "graph_input_type_mismatch"


def test_cancelled_predecessor_carries_succeeded_node_but_not_unsettled_attempt(graph_env):
    graph = graph_env
    run = graph.admission.admit(graph.env.principal, graph.command("graph.admit", graph.payload)).outcome.committed.object_id
    invocation = claim(graph, run)
    complete(graph, run, invocation)
    page = advance(graph, run, maximum=1)
    assert page.status == "running"
    node = next(node for node in page.nodes if node.kind == "invoke")
    assert node.status == "succeeded"
    AuthorityCommands(graph.env.engine).cancel(graph.env.principal, graph.command("runtime.cancel", {"run_id": run, "reason_code": "checkpoint"}))
    reads = SuccessorReads(graph.env.engine)
    cut = reads.sources(graph.env.principal, run, activation_id=node.activation_id)
    assert cut.predecessor_ready
    # New reviewed consumer expects the actual result schema, not the old tool input schema.
    raw = copy.deepcopy(graph.raw)
    shape = raw["body"]["outputs"][0]["value_type"]
    raw["body"] = {"inputs": [{"name": "state", "value_type": shape}], "outputs": [{"name": "state", "value_type": shape}],
        "nodes": [{"kind": "finish", "node_id": "finish", "outputs": [{"port": "state", "source": {"kind": "input", "name": "state"}}]}], "edges": []}
    entry = ReviewedPlan.compile(definition(raw), graph.source.tools, graph.source.schemas)
    service = GraphAdmission(graph.env.engine, PlanCatalog([entry]))
    source = cut.sources[0]
    data = {"plan_sha256": entry.plan.sha256, "inputs": [], "budget": {"limit": 1}, "predecessor": cut.predecessor.model_dump(mode="json"),
        "carried": [{"target_port": "state", "source": source.source.model_dump(mode="json"), "expected_value_sha256": source.value_sha256}]}
    # Inject an incomplete reconciliation cut under the owner role; no fake acceptance claim.
    with graph.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET settled=false WHERE run_id=:run"), {"run": run})
    assert not reads.sources(graph.env.principal, run, activation_id=node.activation_id).predecessor_ready
    assert service.admit_successor(graph.env.principal, graph.command("graph.admit_successor", data)).outcome.reason_code == "predecessor_unsettled"
    with graph.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET settled=true WHERE run_id=:run"), {"run": run})
    accepted = service.admit_successor(graph.env.principal, graph.command("graph.admit_successor", data))
    assert accepted.outcome.status == "accepted", accepted
    assert reads.lineage(graph.env.principal, accepted.outcome.committed.object_id).carried[0].source.activation_id == node.activation_id


def test_authenticated_successor_http_observation_and_replay(graph_env):
    graph = graph_env
    service, payload, run, _, _ = setup(graph)
    credentials = RuntimeCredentials([("s" * 32, graph.env.principal)])
    app = create_app(graph.env.service, credentials, graphs=(service, GraphAdvancer(graph.env.engine)))
    command = graph.command("graph.admit_successor", proposal(graph, payload, run))
    headers = {"Authorization": "Bearer " + "s" * 32}
    with TestClient(app) as client:
        path = f"/v1/graph-runs/{run}/carry-sources"
        assert client.get(path).status_code == 401
        assert client.get(path, headers=headers).json()["predecessor_ready"]
        assert client.get(path + "?activation_id=invalid", headers=headers).status_code == 422
        assert client.post("/v1/graph-runs/successors", content=command.canonical_bytes).status_code == 401
        result = client.post("/v1/graph-runs/successors", content=command.canonical_bytes, headers=headers)
        assert result.status_code == 200, result.text
        assert result.json()["outcome"]["status"] == "accepted"
        assert client.post("/v1/graph-runs/successors", content=command.canonical_bytes, headers=headers).json() == result.json()
        new_run = result.json()["outcome"]["committed"]["object_id"]
        assert client.get(f"/v1/graph-runs/{new_run}/lineage", headers=headers).json()["predecessor"]["run_id"] == run
