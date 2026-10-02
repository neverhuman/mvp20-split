from dataclasses import replace

import pytest
from amphora_contracts_knowledge import GraphAuthoringProfile
from amphora_knowledge.authoring.canonical import digest
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.persistence.ledger import KnowledgeLedger
from amphora_knowledge.transport.api import create_app
from amphora_knowledge.transport.credentials import Credentials
from amphora_knowledge.validation.review import ReferenceReviewer
from amphora_knowledge.validation.transport import PeerUnavailable
from amphora_knowledge.validation.workflow import AuthoringWorkflow
from fastapi.testclient import TestClient

from ..validation.conftest import records

pytestmark = pytest.mark.postgres


@pytest.fixture
def api(stored_graph):
    case = stored_graph
    peer = records(case.proposal)
    reader = replace(case.principal, actor_id="reader", actions=frozenset({"read_graph"}))
    credentials = Credentials([("w"*32, case.principal), ("r"*32, reader)])
    workflow = AuthoringWorkflow(case.ledger, ReferenceReviewer(peer, peer))
    with TestClient(create_app(workflow, credentials)) as client:
        client.headers["Authorization"] = "Bearer " + "w"*32
        yield case, peer, client


def post(client, route, model):
    return client.post(route, content=model.model_dump_json(), headers={"Content-Type": "application/json"})


def test_authenticated_submit_exact_history_reads_and_profile(api):
    case, peer, client = api
    proposal = peer.proposal
    profile = post(client, "/v1/graph-profiles/read", proposal.graph)
    assert profile.status_code == 200
    parsed = GraphAuthoringProfile.model_validate_json(profile.content)
    assert parsed.origin == "configured_default" and digest(parsed.vocabulary) == parsed.vocabulary_reference.sha256
    assert case.ledger.head(case.principal, proposal.graph) is None
    receipt = post(client, "/v1/graph-proposals", proposal)
    assert receipt.status_code == 200
    head = receipt.json()["decision"]["head"]
    assert receipt.json()["decision"]["outcome"] == "accepted"
    assert post(client, "/v1/graph-proposals", proposal).json() == receipt.json()
    assert post(client, "/v1/graph-heads/read", proposal.graph).json() == head
    status = client.get(f"/v1/graphs/{proposal.graph.graph_id}/proposals/{proposal.change_id}")
    assert status.json()["actor_id"] == case.principal.actor_id
    assert status.json()["decision"] == receipt.json()
    for route, reference in [("graph-snapshots", head["snapshot"]), ("graph-changes", head["change"])]:
        result = client.post(f"/v1/{route}/read", json=reference)
        assert result.status_code == 200 and result.json()["reference"] == reference
        assert result.headers["cache-control"] == "no-store"
        reference = dict(reference, sha256="0"*64)
        assert client.post(f"/v1/{route}/read", json=reference).status_code == 404
    # Restart defaults may describe new graphs; existing profile remains pinned.
    changed = KnowledgeLedger(case.engine, case.vocabulary, StructuralPolicy(max_entities=1))
    assert changed.profile(case.principal, proposal.graph).policy == proposal.policy
    assert changed.profile(case.principal, proposal.graph).origin == "stored"


def test_auth_scope_and_action_precede_peer_reads(api):
    case, peer, client = api
    client.headers.pop("Authorization")
    assert post(client, "/v1/graph-proposals", peer.proposal).status_code == 401
    client.headers["Authorization"] = "Bearer " + "r"*32
    assert post(client, "/v1/graph-proposals", peer.proposal).status_code == 403
    assert post(client, "/v1/graph-profiles/read", peer.proposal.graph).status_code == 200
    foreign = peer.proposal.graph.model_copy(update={"scope": case.principal.scope.model_copy(update={"project_id": "other"})})
    assert post(client, "/v1/graph-heads/read", foreign).status_code == 403
    assert not peer.calls


@pytest.mark.parametrize("body,status", [(b'{"a":1,"a":2}', 422), (b'{"x":NaN}', 422),
    (b'\xff', 422), (b'"secret source text"', 422), (b'x'*262145, 413)],
    ids=["duplicate", "nonfinite", "utf8", "wrong_shape", "body_limit"])
def test_malformed_requests_do_not_echo_source(api, body, status):
    _, peer, client = api
    response = client.post("/v1/graph-proposals", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == status
    assert "secret" not in response.text and not peer.calls


def test_caller_cannot_supply_actor_or_validation_authority(api):
    _, peer, client = api
    for name, value in [("actor_id", "owner"), ("validation", {}), ("actions", ["accept"] )]:
        raw = peer.proposal.model_dump(mode="json") | {name: value}
        assert client.post("/v1/graph-proposals", json=raw).status_code == 422
    assert not peer.calls


def test_peer_outage_visible_as_pending_receipt_then_recovery(api, monkeypatch):
    _, peer, client = api
    original = peer.trace

    def unavailable(*args):
        raise PeerUnavailable("peer_unavailable")

    monkeypatch.setattr(peer, "trace", unavailable)
    response = post(client, "/v1/graph-proposals", peer.proposal)
    assert response.status_code == 503 and response.json() == {"code": "reference_review_pending"}
    route = f"/v1/graphs/{peer.proposal.graph.graph_id}/proposals/{peer.proposal.change_id}"
    assert client.get(route).json()["decision"] is None
    monkeypatch.setattr(peer, "trace", original)
    assert post(client, "/v1/graph-proposals", peer.proposal).json()["decision"]["outcome"] == "accepted"
    assert client.get(route).json()["decision"] is not None


def test_changed_same_id_conflicts_and_unknown_status_stays_unknown(api):
    _, peer, client = api
    assert client.get(f"/v1/graphs/{peer.proposal.graph.graph_id}/proposals/missing").status_code == 404
    assert post(client, "/v1/graph-proposals", peer.proposal).status_code == 200
    altered = peer.proposal.model_copy(update={"description": "Changed request"})
    assert post(client, "/v1/graph-proposals", altered).status_code == 409
