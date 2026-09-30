"""Real PostgreSQL API proof; authoring and legacy execution receipt boundaries stay distinct."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.hosting import Host
from amphora_campaign_runtime.inspection.cursors import CursorCodec
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_contracts_core import Scope
from fastapi.testclient import TestClient

from ..scheduling.test_graph_host import graph_host
from .test_commands import command, owner


def test_authoring_routes_scope_revision_receipt_and_explicit_enablement(graph_env):
    graph = graph_env
    e = graph.env
    owner(e)
    credentials = RuntimeCredentials([("a" * 32, e.principal),
        ("r" * 32, replace(e.principal, actions=frozenset({"read"}))),
        ("f" * 32, replace(e.principal, scope=Scope(tenant_id="foreign", project_id="foreign")))])
    args = {"admission": e.service, "credentials": credentials,
        "graphs": (graph.admission, GraphAdvancer(e.engine)), "history": RuntimeHistory(e.engine, CursorCodec("k" * 32))}
    headers = {"Authorization": "Bearer " + "a" * 32}
    route = "/v1/definition-drafts"
    with TestClient(create_app(**args)) as client:
        assert client.get(route, headers=headers).status_code == 404
    with pytest.raises(ValueError, match="explicitly configured graphs"):
        create_app(authoring=True)
    with TestClient(create_app(**args, authoring=True)) as client:
        payload = command(e).canonical_bytes
        assert client.post(route + "/save", content=payload).status_code == 401
        assert client.post(route + "/save", content=payload, headers={"Authorization": "Bearer " + "r" * 32}).status_code == 403
        saved = client.post(route + "/save", content=payload, headers=headers)
        assert saved.status_code == 200 and saved.json()["outcome"]["status"] == "accepted"
        assert client.get("/v1/definition-commands/definition.save/save-1", headers=headers).json() == saved.json()
        assert client.get("/v1/commands/definition.save/save-1", headers=headers).status_code == 404
        original = client.get(route + "/draft", headers=headers).json()
        assert original["head"]["revision"] == 1
        client.post(route + "/save", content=command(e, "second", 1, "Changed").canonical_bytes, headers=headers).raise_for_status()
        assert client.get(route + "/draft", params={"revision": 1}, headers=headers).json() == original
        assert client.get(route, headers=headers).json()["drafts"][0]["revision"] == 2
        foreign = {"Authorization": "Bearer " + "f" * 32}
        assert client.get(route + "/draft", headers=foreign).status_code == 404
        assert client.get(route, headers=foreign).json()["drafts"] == []
        for query in ({"limit": 51}, {"sql": "arbitrary"}):
            assert client.get(route, params=query, headers=headers).status_code == 422
        assert client.get(route + "/draft", params={"revision": 0}, headers=headers).status_code == 422


def test_host_authoring_is_explicit_and_typed(graph_env, tmp_path, monkeypatch):
    path, raw = graph_host(graph_env, tmp_path, monkeypatch)
    raw["authoring"] = True
    raw["principals"][0]["actions"].extend(["author", "validate"])
    path.write_text(json.dumps(raw), encoding="utf-8")
    host = Host.load(path)
    try:
        assert host.authoring is True
        with TestClient(host.app()) as client:
            headers = {"Authorization": "Bearer " + "x" * 32}
            assert client.get("/v1/definition-drafts", headers=headers).status_code == 200
            assert client.post("/v1/definition-drafts/save", content=command(graph_env.env).canonical_bytes, headers=headers).status_code == 200
            draft = client.get("/v1/definition-drafts/draft", headers=headers).json()
            payload = json.loads(command(graph_env.env).canonical_bytes)
            payload["identity"].update(command_family="definition.validate", command_id="validate-http")
            payload["payload"] = {"draft_id": "draft", "revision": 1, "content_sha256": draft["head"]["content_sha256"]}
            response = client.post("/v1/definition-drafts/validate", json=payload, headers=headers)
            response.raise_for_status()
            receipt = response.json()
            assert receipt["outcome"]["status"] == "accepted"
            validation_id = receipt["outcome"]["committed"]["object_id"]
            result = client.get("/v1/definition-validations/" + validation_id, headers=headers)
            assert result.json()["structurally_valid"] and result.json()["scientific_acceptance"] == "not_established"
            assert client.get("/v1/definition-commands/definition.validate/validate-http", headers=headers).json() == receipt
            assert client.get("/v1/definition-validations/" + validation_id).status_code == 401
            assert client.get("/v1/definition-validations/unknown", headers=headers).status_code == 404
            assert client.get("/v1/definition-validations/" + validation_id, params={"unknown": 1}, headers=headers).status_code == 422
    finally:
        host.close()
    for bad in ("true", 1, {}):
        raw["authoring"] = bad
        path.write_text(json.dumps(raw), encoding="utf-8")
        with pytest.raises(ValueError, match="explicitly configured graphs"):
            Host.load(path)
