from dataclasses import replace

import pytest
from amphora_knowledge.transport.api import create_app
from amphora_knowledge.transport.credentials import Credentials
from amphora_knowledge.validation.transport import PeerUnavailable
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


def test_authenticated_reasoning_http_status_replay_and_denied_writer(reasoning_case):
    c = reasoning_case
    reader = replace(c.principal, actor_id="reader", actions=frozenset({"read_graph"}))
    credentials = Credentials([("w"*32, c.principal), ("r"*32, reader)])
    with TestClient(create_app(c.authoring, credentials, c.workflow)) as client:
        response = client.post("/v1/graph-reasoning", json=c.request.model_dump(mode="json"))
        assert response.status_code == 401
        client.headers["Authorization"] = "Bearer " + "w"*32
        response = client.post("/v1/graph-reasoning", json=c.request.model_dump(mode="json"))
        assert response.status_code == 200 and response.json()["decision"]["outcome"] == "evaluated"
        assert response.headers["cache-control"] == "no-store"
        assert client.post("/v1/graph-reasoning", json=c.request.model_dump(mode="json")).json() == response.json()
        client.headers["Authorization"] = "Bearer " + "r"*32
        assert client.post("/v1/graph-reasoning", json=c.request.model_dump(mode="json")).status_code == 403
        assert client.get(f"/v1/graphs/{c.request.snapshot.graph.graph_id}/reasoning/reason").json() == response.json()
        assert client.get(f"/v1/graphs/{c.request.snapshot.graph.graph_id}/reasoning/missing").status_code == 404


def test_http_outage_exposes_pending_reconciliation(reasoning_case, monkeypatch):
    c = reasoning_case
    def outage(*args):
        raise PeerUnavailable("peer_unavailable")

    monkeypatch.setattr(c.reviewer, "review_reasoning", outage)
    credentials = Credentials([("w"*32, c.principal)])
    with TestClient(create_app(c.authoring, credentials, c.workflow)) as client:
        client.headers["Authorization"] = "Bearer " + "w"*32
        assert client.post("/v1/graph-reasoning", json=c.request.model_dump(mode="json")).status_code == 503
        response = client.get(f"/v1/graphs/{c.request.snapshot.graph.graph_id}/reasoning/reason")
        assert response.status_code == 200 and response.json()["decision"] is None
