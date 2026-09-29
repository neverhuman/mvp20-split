"""Configured public wait HTTP contracts; TestClient is not installed issuer acceptance."""

from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from fastapi.testclient import TestClient

from ..completion.test_acceptance import Peer
from .test_execution import start, submit_command


def test_receipt_authentication_versioned_observation_and_exact_http_replay(graph_env):
    f = start(graph_env)
    credentials = RuntimeCredentials([("o" * 32, graph_env.env.principal), ("i" * 32, f.issuer)])
    app = create_app(graph_env.env.service, credentials, CompletionCoordinator(graph_env.env.engine, Peer()),
                     graphs=(f.admission, f.advance))
    command = submit_command(f)
    issuer = {"Authorization": "Bearer " + "i" * 32}
    owner = {"Authorization": "Bearer " + "o" * 32}
    with TestClient(app) as client:
        assert client.post("/v1/graph-receipts", content=command.canonical_bytes).status_code == 401
        assert client.post("/v1/graph-receipts", content=command.canonical_bytes, headers=owner).status_code == 403
        assert client.get(f"/v1/graph-runs/{f.run}", headers=issuer).status_code == 409
        observed = client.get(f"/v2/graph-runs/{f.run}", headers=issuer)
        assert observed.status_code == 200 and observed.json()["schema_version"] == "2"
        assert any(node["kind"] == "await" for node in observed.json()["nodes"])
        path = f"/v1/graph-runs/{f.run}/waits/{f.activation}"
        opened = client.get(path, headers=issuer)
        assert opened.status_code == 200 and opened.json()["closure"] is None
        assert client.get(f"/v1/graph-runs/foreign/waits/{f.activation}", headers=issuer).status_code == 404
        first = client.post("/v1/graph-receipts", content=command.canonical_bytes, headers=issuer)
        assert first.status_code == 200 and first.json()["outcome"]["status"] == "accepted"
        assert client.post("/v1/graph-receipts", content=command.canonical_bytes, headers=issuer).json() == first.json()
        assert client.get(path, headers=issuer).json()["closure"]["outcome"]["status"] == "accepted"
