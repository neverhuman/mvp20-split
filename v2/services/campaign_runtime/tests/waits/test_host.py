"""V3 definitions load from exact schema pins and require a configured protection peer."""

import json

import pytest
from amphora_campaign_runtime.hosting import Host
from export_schemas import ROOT

from ..compiler.conftest import FIXTURES
from ..scheduling.test_graph_host import graph_host


def test_await_only_host_loads_v3_and_requires_artifact_protection(graph_env, tmp_path, monkeypatch):
    path, raw = graph_host(graph_env, tmp_path, monkeypatch)
    definition = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())[0]["payload"]
    definition["scope"] = graph_env.env.principal.scope.model_dump(mode="json")
    (tmp_path / "await.json").write_text(json.dumps(definition), encoding="utf-8")
    schemas = []
    for kind in ("input", "output"):
        (tmp_path / (kind + ".json")).write_bytes((FIXTURES / (kind + ".json")).read_bytes())
        ref = getattr(graph_env.source.tool.lock, kind + "_schemas")[0].schema_ref
        schemas.append({"schema_ref": ref.model_dump(mode="json"), "path": kind + ".json"})
    raw["graphs"] = [{"definition": "await.json", "releases": [], "schemas": schemas}]
    raw["principals"][0]["actions"].append("submit_receipt")
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="completion peer"):
        Host.load(path)
    raw["artifacts"] = {"runtime_owner": "runtime", "reserve_endpoint": "http://127.0.0.1:1/reservations",
                        "token_env": "TEST_RUNTIME_TOKEN"}
    path.write_text(json.dumps(raw), encoding="utf-8")
    host = Host.load(path)
    try:
        assert "submit_receipt" in host.principals[0].actions
        routes = {route.path for route in host.app().routes}
        assert {"/v1/graph-receipts", "/v2/graph-runs/{run_id}", "/v1/graph-runs/{run_id}/waits/{activation_id}"} <= routes
    finally:
        host.close()
