"""Configured graph HTTP and polling with real owner persistence; not installed-peer acceptance."""

import json

import pytest
from amphora_campaign_runtime.coordinator.polling import GraphPoller
from amphora_campaign_runtime.hosting import Host
from fastapi.testclient import TestClient

from ..lifecycle.test_host_reads import config


def graph_host(graph, tmp_path, monkeypatch):
    path, raw = config(graph.env, tmp_path, monkeypatch)
    definition = graph.source.raw[3]
    definition["scope"] = graph.env.principal.scope.model_dump(mode="json")
    (tmp_path / "loop.json").write_text(json.dumps(definition), encoding="utf-8")
    raw["fixtures"] = []
    raw["principals"][0]["actions"].append("maintain")
    raw["graphs"] = [{"definition": "loop.json", "releases": [], "schemas": []}]
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path, raw


def test_graph_only_host_admission_advance_observation_and_polling(graph_env, tmp_path, monkeypatch):
    graph = graph_env
    path, raw = graph_host(graph, tmp_path, monkeypatch)
    host = Host.load(path)
    try:
        from amphora_campaign_runtime.coordinator import ReviewedPlan

        from ..compiler.conftest import definition
        entry = ReviewedPlan.compile(definition(graph.source.raw[3]), graph.source.tools, graph.source.schemas)
        command = graph.command("graph.admit", {"plan_sha256": entry.plan.sha256, "inputs": [], "budget": {"limit": 2}})
        with TestClient(host.app()) as client:
            headers = {"Authorization": "Bearer " + "x" * 32}
            assert client.get("/health").json()["execution_available"] is True
            assert client.get("/ready").json()["mode"] == "configured_graphs"
            assert client.post("/v1/graph-runs", content=command.canonical_bytes).status_code == 401
            response = client.post("/v1/graph-runs", content=command.canonical_bytes, headers=headers)
            assert response.status_code == 200
            run = response.json()["outcome"]["committed"]["object_id"]
            advance = graph.command("graph.advance", {"run_id": run, "max_transitions": 1})
            assert client.post("/v1/graph-runs/advance", content=advance.canonical_bytes, headers=headers).status_code == 200
            assert client.get(f"/v1/graph-runs/{run}?limit=101", headers=headers).status_code == 422
            assert client.get("/v1/graph-runs/foreign", headers=headers).status_code == 404
            poller = GraphPoller(host.admission.commands.engine, host.graphs[1])
            assert poller.tick(host.principals[0]) is True
            assert poller.tick(host.principals[0]) is False
            page = client.get(f"/v1/graph-runs/{run}", headers=headers).json()
            assert page["status"] == "completed" and page["node_count"] == 4
    finally:
        host.close()


@pytest.mark.parametrize("mutation", ["empty", "extra", "bad-definition", "bad-projection"])
def test_invalid_graph_configuration_never_starts(graph_env, tmp_path, monkeypatch, mutation):
    path, raw = graph_host(graph_env, tmp_path, monkeypatch)
    if mutation == "empty":
        raw["graphs"] = []
    elif mutation == "extra":
        raw["graphs"][0]["guess"] = True
    elif mutation == "bad-definition":
        (tmp_path / "loop.json").write_text('{}', encoding="utf-8")
    else:
        raw["projections"] = {"endpoint": "https://invalid", "token_env": "TEST_RUNTIME_TOKEN", "unexpected": True}
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        Host.load(path)


def test_tool_graph_loads_exact_public_pins_and_requires_completion_peer(graph_env, tmp_path, monkeypatch):
    from ..compiler.conftest import FIXTURES
    graph = graph_env
    path, raw = graph_host(graph, tmp_path, monkeypatch)
    (tmp_path / "tool.json").write_text(json.dumps(graph.raw), encoding="utf-8")
    (tmp_path / "release.json").write_bytes((FIXTURES / "numeric-release.json").read_bytes())
    schemas = []
    for kind in ("input", "output"):
        (tmp_path / (kind + ".json")).write_bytes((FIXTURES / (kind + ".json")).read_bytes())
        reference = getattr(graph.source.tool.lock, kind + "_schemas")[0].schema_ref
        schemas.append({"schema_ref": reference.model_dump(mode="json"), "path": kind + ".json"})
    raw["graphs"] = [{"definition": "tool.json", "releases": [{"descriptor": "release.json",
                       "lock": graph.source.tool.lock.model_dump(mode="json")}], "schemas": schemas}]
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="completion peer"):
        Host.load(path)
    raw["artifacts"] = {"runtime_owner": "runtime", "reserve_endpoint": "http://127.0.0.1:1/reservations", "token_env": "TEST_RUNTIME_TOKEN"}
    path.write_text(json.dumps(raw), encoding="utf-8")
    host = Host.load(path)
    try:
        assert host.graphs[0].catalog.needs_completion
        assert host.graphs[0].catalog.require(graph.env.principal.scope, graph.entry.plan.sha256).plan == graph.entry.plan
    finally:
        host.close()
    (tmp_path / "input.json").write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="schema_digest_mismatch"):
        Host.load(path)
