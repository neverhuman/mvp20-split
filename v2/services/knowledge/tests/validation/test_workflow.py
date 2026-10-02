import pytest
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.validation.review import ReferenceReviewer
from amphora_knowledge.validation.transport import PeerUnavailable
from amphora_knowledge.validation.workflow import AuthoringWorkflow

pytestmark = pytest.mark.postgres


def test_intent_survives_peer_outage_then_exact_retry_accepts(persisted_peers, monkeypatch):
    case, peer = persisted_peers.store, persisted_peers.peers
    workflow = AuthoringWorkflow(case.ledger, ReferenceReviewer(peer, peer))
    original = peer.source

    def unavailable(*args):
        status = case.ledger.status(case.principal, peer.proposal.graph, peer.proposal.change_id)
        assert status is not None and status.decision is None
        raise PeerUnavailable("peer_unavailable")

    monkeypatch.setattr(peer, "source", unavailable)
    with pytest.raises(PeerUnavailable):
        workflow.submit(case.principal, peer.proposal)
    assert case.ledger.head(case.principal, peer.proposal.graph) is None
    monkeypatch.setattr(peer, "source", original)
    accepted = workflow.submit(case.principal, peer.proposal)
    assert accepted.decision.outcome == "accepted"
    monkeypatch.setattr(peer, "source", unavailable)
    assert workflow.submit(case.principal, peer.proposal) == accepted


def test_denied_reference_becomes_stable_auditable_rejection(persisted_peers, monkeypatch):
    case, peer = persisted_peers.store, persisted_peers.peers
    workflow = AuthoringWorkflow(case.ledger, ReferenceReviewer(peer, peer))

    def denied(*args):
        raise KnowledgeError("peer_access_denied")

    monkeypatch.setattr(peer, "content", denied)
    result = workflow.submit(case.principal, peer.proposal)
    assert result.decision.outcome == "rejected"
    assert result.decision.findings[0].code == "peer_access_denied"
    assert workflow.submit(case.principal, peer.proposal) == result
    assert case.ledger.head(case.principal, peer.proposal.graph) is None
