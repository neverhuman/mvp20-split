"""Real owner HTTP contracts enforce permission, strict filters and bounded reads."""

from dataclasses import replace

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from fastapi.testclient import TestClient

from ..graph_inspection.test_snapshots import start


def test_navigation_http_authorization_and_unknown_filter_rejection(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    token = snapshots.page(graph.env.principal, run).snapshot.snapshot_token
    credentials = RuntimeCredentials([("r" * 32, graph.env.principal),
        ("d" * 32, replace(graph.env.principal, actions=frozenset()))])
    app = create_app(graph.env.service, credentials, graphs=(graph.admission, GraphAdvancer(graph.env.engine)),
                     history=RuntimeHistory(graph.env.engine, cursors))
    headers = {"Authorization": "Bearer " + "r" * 32}
    route = f"/v1/graph-observations/{run}/scopes"
    with TestClient(app) as client:
        assert client.get(route, params={"snapshot_token": token}).status_code == 401
        assert client.get(route, params={"snapshot_token": token}, headers={"Authorization": "Bearer " + "d" * 32}).status_code == 403
        assert client.get(route, params={"snapshot_token": token, "sql": "arbitrary"}, headers=headers).status_code == 422
        scopes = client.get(route, params={"snapshot_token": token}, headers=headers)
        assert scopes.status_code == 200
        topology = route + "/" + scopes.json()["scopes"][0]["scope_key"] + "/topology"
        for extra in ({"unknown_filter": "x"}, {"radius": 3}, {"limit": 101}):
            assert client.get(topology, params={"snapshot_token": token, **extra}, headers=headers).status_code == 422
        result = client.get(topology, params={"snapshot_token": token}, headers=headers)
        assert result.status_code == 200 and len(result.json()["edges"]) == 1
        assert result.json()["cut"] == scopes.json()["cut"]
        catalog = f"/v1/graph-observations/{run}/views"
        assert client.get(catalog, params={"snapshot_token": token}, headers=headers).json()["cut"] == scopes.json()["cut"]
        assert client.get(catalog, params={"snapshot_token": token, "view": "arbitrary"}, headers=headers).status_code == 422
        assert client.get(catalog, params={"snapshot_token": token}).status_code == 401
