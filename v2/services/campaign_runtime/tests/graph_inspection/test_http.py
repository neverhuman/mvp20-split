"""Authenticated explicit opt-in graph observations and resnapshot errors."""

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.inspection.cursors import CursorCodec
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from fastapi.testclient import TestClient

from ..scheduling.test_advancement import advance, claim, complete
from .test_snapshots import start


def test_http_snapshot_and_invalidation_surface_requires_graphs_and_history(graph_env):
    graph = graph_env
    run, cursors, _ = start(graph)
    credentials = RuntimeCredentials([("g" * 32, graph.env.principal)])
    graphs = graph.admission, GraphAdvancer(graph.env.engine)
    no_history = create_app(graph.env.service, credentials, graphs=graphs)
    assert not any(path.startswith("/v1/graph-observations") for path in no_history.openapi()["paths"])
    app = create_app(graph.env.service, credentials, graphs=graphs, history=RuntimeHistory(graph.env.engine, cursors))
    headers = {"Authorization": "Bearer " + "g" * 32}
    with TestClient(app) as client:
        path = f"/v1/graph-observations/{run}"
        assert client.get(path + "/nodes").status_code == 401
        assert client.get(path + "/nodes", headers=headers, params={"limit": 101}).status_code == 422
        first = client.get(path + "/nodes", headers=headers, params={"limit": 1}).json()
        detail = client.get(path + "/nodes/" + first["nodes"][0]["activation_id"], headers=headers,
            params={"snapshot_token": first["snapshot"]["snapshot_token"]})
        assert detail.status_code == 200 and detail.json()["cut"] == first["snapshot"]["cut"]
        invocation = claim(graph, run)
        stale = client.get(path + "/nodes", headers=headers, params={"cursor": first["next_cursor"]})
        assert stale.status_code == 409 and stale.json() == {"reason_code": "snapshot_unavailable", "resnapshot": True}
        events = client.get(path + "/invalidations", headers=headers, params={"cursor": first["snapshot"]["event_cursor"]})
        assert events.status_code == 200 and events.json()["entries"][0]["kind"] == "run_changed"
        tampered = client.get(path + "/invalidations", headers=headers, params={"cursor": "bad"})
        assert tampered.status_code == 409 and tampered.json()["resnapshot"]
        assert client.get("/v1/graph-observations/foreign/nodes", headers=headers).status_code == 404
        complete(graph, run, invocation)
        advance(graph, run)
        fresh = client.get(path + "/nodes", headers=headers).json()
        output = client.get(path + "/nodes/" + invocation.activation_id + "/outputs/result", headers=headers,
            params={"snapshot_token": fresh["snapshot"]["snapshot_token"]})
        assert output.status_code == 200 and output.json()["items"][0]["value"]["kind"] == "artifact"


def test_cursor_key_rotation_requires_resnapshot(graph_env):
    graph = graph_env
    run, _, snapshots = start(graph)
    first = snapshots.page(graph.env.principal, run, limit=1)
    import pytest
    from amphora_campaign_runtime.graph_inspection.snapshots import GraphSnapshots
    from amphora_campaign_runtime.inspection.cursors import InspectionError
    replacement = GraphSnapshots(graph.env.engine, CursorCodec("different-signing-key-" * 3))
    with pytest.raises(InspectionError, match="invalid_cursor"):
        replacement.page(graph.env.principal, run, cursor=first.next_cursor)
