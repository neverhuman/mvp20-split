from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_knowledge import ReasoningPublicationRequest
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.publication.identity import PublisherIdentity
from amphora_knowledge.publication.store import PUBLICATION_SCOPE, PublicationStore
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def begin(c):
    return c.publications.begin(c.principal, c.publication, c.publisher)


def test_intent_survives_replacement_with_exact_publisher_binding(publication_case):
    c = publication_case
    original = begin(c)
    replacement = PublicationStore(c.case.engine)
    assert replacement.begin(c.principal, c.publication, c.publisher) == original
    with c.case.engine.connect() as connection:
        source = replacement.source(connection, original)
    assert source.status.decision.result.request == c.request
    with pytest.raises(KnowledgeError, match="publication_binding_conflict"):
        replacement.begin(c.principal, c.publication, PublisherIdentity("different-publisher", c.publisher.issuer_id))


@pytest.mark.parametrize("variant", ["actor", "request"])
def test_existing_intent_rejects_identity_reuse(publication_case, variant):
    c = publication_case
    begin(c)
    principal, request = c.principal, c.publication
    if variant == "actor":
        principal = replace(principal, actor_id="other")
    else:
        request = request.model_copy(update={"reasoning_request_id": "other"})
    with pytest.raises(KnowledgeError, match="publication_identity_conflict"):
        c.publications.begin(principal, request, c.publisher)


def test_cannot_select_another_actors_result_or_missing_result(publication_case):
    c = publication_case
    with pytest.raises(KnowledgeError, match="publication_reasoning_mismatch"):
        c.publications.begin(replace(c.principal, actor_id="other"), c.publication, c.publisher)
    with pytest.raises(KnowledgeError, match="publication_reasoning_missing"):
        c.publications.begin(c.principal, c.publication.model_copy(update={"reasoning_request_id": "missing"}), c.publisher)
    with pytest.raises(KnowledgeError, match="publication_intent_missing"):
        c.publications.acquire(c.principal, c.publication)


def test_pending_reasoning_cannot_register_publication(reasoning_case):
    c = reasoning_case
    c.store.begin(c.principal, c.request, c.profile)
    principal = replace(c.principal, actions=frozenset({"publish_reasoning"}))
    request = ReasoningPublicationRequest(wire_version="1", graph=c.request.snapshot.graph,
        publication_id="publish", reasoning_request_id=c.request.request_id)
    store = PublicationStore(c.case.engine)
    with pytest.raises(KnowledgeError, match="publication_reasoning_pending"):
        store.begin(principal, request, PublisherIdentity("publisher", "issuer"))
    with pytest.raises(KnowledgeError, match="publication_intent_missing"):
        store.acquire(principal, request)


def test_duplicate_intents_and_concurrent_claims_have_one_lease(publication_case):
    c = publication_case
    barrier = Barrier(2)

    def contender(_):
        barrier.wait(timeout=5)
        document = begin(c)
        return document, c.publications.acquire(c.principal, c.publication)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(contender, range(2)))
    assert results[0][0] == results[1][0]
    leases = [lease for _, lease in results if lease is not None]
    assert len(leases) == 1 and leases[0].fence == 1
    c.publications.release(leases[0])
    successor = c.publications.acquire(c.principal, c.publication)
    assert successor.fence == 2 and successor.holder != leases[0].holder
    for operation in (c.publications.renew, c.publications.release):
        with pytest.raises(KnowledgeError, match="publication_lease_lost"):
            operation(leases[0])


def test_expiry_uses_database_clock_and_cannot_be_renewed(publication_case):
    c = publication_case
    begin(c)
    old = c.publications.acquire(c.principal, c.publication, seconds=1)
    # Hold the row while the original deadline passes. A waiter must compare
    # the clock after acquiring the lock, not at its transaction start.
    with c.case.engine.begin() as connection:
        connection.execute(text("SELECT fence FROM knowledge.publication_leases WHERE " + PUBLICATION_SCOPE + " FOR UPDATE"), old.key)
        with ThreadPoolExecutor(max_workers=1) as pool:
            waiting = pool.submit(c.publications.renew, old)
            connection.execute(text("SELECT pg_sleep(1.1)"))
            connection.commit()
            with pytest.raises(KnowledgeError, match="publication_lease_lost"):
                waiting.result(timeout=5)
    new = c.publications.acquire(c.principal, c.publication)
    assert new.fence == old.fence + 1
    renewed = c.publications.renew(new, seconds=120)
    assert renewed.fence == new.fence and renewed.expires_at > new.expires_at


@pytest.mark.parametrize("duration", [0, 301, True, 1.5])
def test_invalid_lease_duration_has_no_effect(publication_case, duration):
    c = publication_case
    begin(c)
    with pytest.raises(KnowledgeError, match="publication_lease_duration_invalid"):
        c.publications.acquire(c.principal, c.publication, seconds=duration)
    assert c.publications.acquire(c.principal, c.publication).fence == 1


def test_intent_and_lease_registration_are_atomic(publication_case):
    c = publication_case

    def interrupt(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO knowledge.publication_leases"):
            raise RuntimeError("lease insertion interrupted")

    event.listen(c.case.engine, "before_cursor_execute", interrupt)
    try:
        with pytest.raises(RuntimeError, match="interrupted"):
            begin(c)
    finally:
        event.remove(c.case.engine, "before_cursor_execute", interrupt)
    with pytest.raises(KnowledgeError, match="publication_intent_missing"):
        c.publications.acquire(c.principal, c.publication)
    begin(c)
    assert c.publications.acquire(c.principal, c.publication).fence == 1


@pytest.mark.parametrize("statement", [
    "UPDATE knowledge.reasoning_publications SET issuer_id='rewrite'",
    "DELETE FROM knowledge.reasoning_publications",
    "DELETE FROM knowledge.publication_leases",
    "UPDATE knowledge.publication_leases SET publication_id='rewrite'",
])
def test_service_cannot_rewrite_intent_or_lease_identity(publication_case, statement):
    c = publication_case
    document = begin(c)
    with pytest.raises(DBAPIError):
        with c.case.engine.begin() as connection:
            connection.execute(text(statement + " WHERE " + PUBLICATION_SCOPE), document.key)
