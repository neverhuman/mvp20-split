from dataclasses import replace

import pytest
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.publication.store import PUBLICATION_SCOPE, PublicationStore
from amphora_knowledge.publication.workflow import PublicationWorkflow
from amphora_knowledge.transport.api import create_app
from amphora_knowledge.transport.credentials import Credentials
from amphora_knowledge.validation.transport import PeerUnavailable
from amphora_tool_protocol import TransportLost
from fastapi.testclient import TestClient
from sqlalchemy import text

from .peer_fixture import PublicationPeer

pytestmark = pytest.mark.postgres


@pytest.fixture
def publishing(publication_case):
    c = publication_case
    c.data = PublicationPeer()
    c.publishing = PublicationWorkflow(c.publications, c.reviewer, c.publisher, c.data)
    return c


def submit(c):
    return c.publishing.submit(c.principal, c.publication)


def test_success_uses_public_sdk_and_replay_never_reads_peers(publishing, monkeypatch):
    c = publishing
    observed = []
    review = c.reviewer.review_reasoning

    def fresh(*args):
        result = review(*args)
        observed.append(result)
        return result

    monkeypatch.setattr(c.reviewer, "review_reasoning", fresh)
    status = submit(c)
    assert status.outcome.status == "published" and len(observed) == 1
    progress = c.publishing.journal.read(c.principal, c.publication)
    assert progress.payload.artifact.observation == observed[0]
    assert c.data.bytes["upload-1"] == progress.payload.artifact.body
    assert set(progress.payload.artifact.declaration.inputs) == set(observed[0].artifacts)

    def no_peer(*args, **kwargs):
        raise AssertionError("historical publication replay cannot consume peers")

    monkeypatch.setattr(c.reviewer, "review_reasoning", no_peer)
    monkeypatch.setattr(c.data, "request", no_peer)
    c.publishing = PublicationWorkflow(PublicationStore(c.case.engine), c.reviewer, c.publisher, c.data)
    assert submit(c) == status


def test_lost_begin_and_finalize_acknowledgements_reconcile_original_commands(publishing):
    c = publishing
    c.data.drop_begin = c.data.drop_finalize = True
    status = submit(c)
    assert status.outcome.status == "published"
    assert len(c.data.uploads) == len(c.data.derivations) == 1
    assert sum(method == "POST" for method, _ in c.data.calls) == 2
    assert sum(method == "PUT" for method, _ in c.data.calls) == 1


def test_lost_stream_ack_requires_new_upload_and_retains_old_uncertainty(publishing):
    c = publishing
    c.data.drop_stream = True
    with pytest.raises(TransportLost):
        submit(c)
    old = c.publishing.journal.read(c.principal, c.publication)
    assert old.attempt.stage == "streaming" and "upload-1" in c.data.bytes
    c.publishing = PublicationWorkflow(PublicationStore(c.case.engine), c.reviewer, c.publisher, c.data)
    status = submit(c)
    assert status.outcome.status == "published" and status.outcome.derivation.upload_id == "upload-2"
    assert len(c.data.bytes) == 2 and len(c.data.derivations) == 1
    assert c.publishing.journal.read(c.principal, c.publication).attempt.identity.ordinal == 2


def test_repeated_ambiguous_puts_stop_at_eight_attempts(publishing):
    c = publishing
    for ordinal in range(1, 9):
        c.data.drop_stream = True
        with pytest.raises(TransportLost):
            submit(c)
        assert c.publishing.journal.read(c.principal, c.publication).attempt.identity.ordinal == ordinal
    status = submit(c)
    assert status.outcome.status == "failed" and status.outcome.code == "publication_stream_attempt_limit"
    assert status.outcome.external_effects == "possible"
    assert len(c.data.uploads) == len(c.data.bytes) == 8 and not c.data.derivations


def test_lease_replacement_during_put_prevents_late_finalize(publishing):
    c = publishing
    successor = []

    def replace_lease():
        progress = c.publishing.journal.read(c.principal, c.publication)
        if progress.attempt.stage != "streaming" or successor:
            return
        document = c.publications.begin(c.principal, c.publication, c.publisher)
        with c.case.engine.begin() as connection:
            connection.execute(text("UPDATE knowledge.publication_leases SET expires_at=clock_timestamp()-interval '1 second' WHERE " +
                                    PUBLICATION_SCOPE), document.key)
        successor.append(c.publications.acquire(c.principal, c.publication))

    c.data.before_request = replace_lease
    with pytest.raises(KnowledgeError, match="publication_lease_lost"):
        submit(c)
    assert c.publishing.journal.read(c.principal, c.publication).attempt.stage == "streaming"
    assert len(c.data.bytes) == 1 and not c.data.derivations
    c.data.before_request = lambda: None
    c.publications.release(successor[0])
    assert submit(c).outcome.derivation.upload_id == "upload-2"


def test_data_finalize_before_knowledge_interruption_recovers_without_republication(publishing, monkeypatch):
    c = publishing

    def interrupted(*args, **kwargs):
        raise RuntimeError("owner interrupted before terminal commit")

    monkeypatch.setattr(c.publishing.terminals, "finish", interrupted)
    with pytest.raises(RuntimeError, match="interrupted"):
        submit(c)
    assert len(c.data.derivations) == 1
    posts = sum(method == "POST" for method, _ in c.data.calls)
    c.publishing = PublicationWorkflow(PublicationStore(c.case.engine), c.reviewer, c.publisher, c.data)
    assert submit(c).outcome.status == "published"
    assert sum(method == "POST" for method, _ in c.data.calls) == posts


def test_review_outage_leaves_no_payload_and_denial_has_no_external_effects(publishing, monkeypatch):
    c = publishing

    def unavailable(*args):
        raise PeerUnavailable("peer_unavailable")

    monkeypatch.setattr(c.reviewer, "review_reasoning", unavailable)
    with pytest.raises(PeerUnavailable):
        submit(c)
    assert c.publishing.read(c.principal, c.publication).outcome.status == "pending"
    assert c.publishing.journal.read(c.principal, c.publication) is None
    assert c.data.calls == []

    def denied(*args):
        raise KnowledgeError("peer_access_denied")

    monkeypatch.setattr(c.reviewer, "review_reasoning", denied)
    status = submit(c)
    assert status.outcome.status == "failed" and status.outcome.external_effects == "none"
    assert c.data.calls == []


def test_finalize_rights_rejection_retains_original_data_proof(publishing):
    c = publishing
    c.data.deny_finalize = True
    status = submit(c)
    assert status.outcome.status == "failed" and status.outcome.code == "rights_revoked"
    assert status.outcome.external_effects == "possible"
    assert c.publishing.read(c.principal, c.publication) == status


def test_busy_lease_returns_pending_without_peer_calls(publishing):
    c = publishing
    c.publications.begin(c.principal, c.publication, c.publisher)
    lease = c.publications.acquire(c.principal, c.publication)
    try:
        assert submit(c).outcome.status == "pending"
        assert c.data.calls == []
    finally:
        c.publications.release(lease)


def test_no_owner_sql_transaction_remains_open_during_data_io(publishing):
    c = publishing

    def check():
        with c.case.engine.connect() as connection:
            count = connection.execute(text("SELECT count(*) FROM pg_stat_activity WHERE usename=current_user "
                "AND pid<>pg_backend_pid() AND state='idle in transaction' AND datname=current_database()" )).scalar_one()
        assert count == 0

    c.data.before_request = check
    assert submit(c).outcome.status == "published"


def test_optional_api_authentication_and_publication_status(publishing):
    c = publishing
    token = "publication-token-" + "x" * 32
    other = replace(c.principal, actions=frozenset({"read_graph"}))
    credentials = Credentials(((token, c.principal), ("reader-token-" + "x" * 32, other)))
    with TestClient(create_app(c.authoring, credentials, publication=c.publishing)) as client:
        path, payload = "/v1/reasoning-publications", c.publication.model_dump(mode="json")
        assert client.post(path, json=payload).status_code == 401
        assert client.post(path, json=payload, headers={"Authorization": "Bearer reader-token-" + "x" * 32}).status_code == 403
        headers = {"Authorization": "Bearer " + token}
        assert client.post(path + "/read", json=payload, headers=headers).status_code == 404
        bad = dict(payload, actor_id="injected")
        assert client.post(path, json=bad, headers=headers).status_code == 422
        published = client.post(path, json=payload, headers=headers)
        assert published.status_code == 200 and published.json()["outcome"]["status"] == "published"
        assert client.post(path + "/read", json=payload, headers=headers).json() == published.json()
    with TestClient(create_app(c.authoring, credentials)) as client:
        assert client.post(path, json=payload, headers=headers).status_code == 404
