"""Actual Planning PostgreSQL; Data receipts are scripted in this tier."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.publication.journal import PublicationJournal
from amphora_agent_planning.publication.store import PublicationStore
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from ..source_access.test_review import inputs
from .test_values import prepared, receipts

pytestmark = pytest.mark.postgres


def setup(s):
    identity, projection, review, artifact = prepared(s.principal.scope)
    _, data = inputs(scope=s.principal.scope)
    class Provider:
        def supports(self, model):
            return True
        def reply(self, binding):
            return ProviderReply((json.dumps(data.draft).encode(),), unknown_usage())
    s.journal.register(s.principal, review.task.request)
    extractions = ExtractionJournal(s.engine)
    extractions.register(s.principal, review.task)
    binding = AttemptBinding(review.task.request, 1)
    s.journal.begin_attempt(s.principal, binding)
    s.journal.record(s.principal, binding, observe(binding, Provider()))
    stored = extractions.record(s.principal, review.task.document().task_id, binding.reference(), "trace")
    assert stored.projection == projection
    store = PublicationStore(s.engine, "data-owner")
    assert store.register(s.principal, "publication", projection.reference()) == identity
    return store, PublicationJournal(store), identity, review, artifact


def test_preparation_transition_history_and_replacement_preserve_exact_bytes_and_time(stored):
    s = stored
    store, journal, identity, review, artifact = setup(s)
    assert store.register(s.principal, "publication", identity.trace()) == identity
    assert journal.read(s.principal, "missing") is None
    initial = journal.read(s.principal, "publication")
    assert initial.position == 0 and initial.payload is None
    lease = store.acquire(s.principal, "publication")
    state = journal.prepare(s.principal, lease, review)
    assert state.payload.artifact == artifact and state.position == 1
    assert journal.prepare(s.principal, lease, review) == state
    first_time = state.prepared_at
    upload, stream, final, derivation = receipts(identity, artifact, state.attempt)
    for action, data in [("begun", upload.model_dump(mode="json")), ("streaming", None),
                         ("streamed", stream.model_dump(mode="json")), ("finalizing", None),
                         ("finalized", {"receipt": final.model_dump(mode="json"),
                                        "derivation": derivation.model_dump(mode="json")})]:
        state = journal.advance(s.principal, lease, state.position, action, data)
    assert state.position == 6 and state.attempt.result == derivation and state.prepared_at == first_time
    replacement = create_engine(s.engine.url)
    try:
        rebuilt = PublicationJournal(PublicationStore(replacement, "data-owner"))
        assert rebuilt.read(s.principal, "publication") == state
        reader = replace(s.principal, actions=frozenset({"read_attempts"}))
        assert rebuilt.read(reader, "publication") == state  # No synthetic write grants on readback.
    finally:
        replacement.dispose()
    renewed = store.renew(s.principal, lease, 60)
    assert renewed.fence == lease.fence and renewed.expires_at > lease.expires_at
    store.release(s.principal, renewed)
    next_lease = store.acquire(s.principal, "publication")
    assert next_lease.fence == lease.fence + 1 and next_lease.holder != lease.holder


def test_concurrent_lease_and_stream_intent_have_one_winner(stored):
    s = stored
    store, journal, identity, review, artifact = setup(s)
    barrier = Barrier(2)
    def acquire():
        barrier.wait(5)
        try:
            return store.acquire(s.principal, "publication")
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [f.result(10) for f in [pool.submit(acquire), pool.submit(acquire)]]
    assert results.count("publication_lease_unavailable") == 1
    lease = next(value for value in results if not isinstance(value, str))
    state = journal.prepare(s.principal, lease, review)
    upload, _, _, _ = receipts(identity, artifact, state.attempt)
    state = journal.advance(s.principal, lease, state.position, "begun", upload.model_dump(mode="json"))
    barrier = Barrier(2)
    def stream_intent():
        barrier.wait(5)
        try:
            return journal.advance(s.principal, lease, state.position, "streaming")
        except ValueError as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [f.result(10) for f in [pool.submit(stream_intent), pool.submit(stream_intent)]]
    assert results.count("publication_position_conflict") == 1
    assert journal.read(s.principal, "publication").attempt.stage == "streaming"


def test_expired_holder_cannot_advance_renew_release_or_prepare(stored):
    s = stored
    store, journal, _, review, _ = setup(s)
    stale = store.acquire(s.principal, "publication", 1)
    original = journal.prepare(s.principal, stale, review)
    time.sleep(1.1)
    current = store.acquire(s.principal, "publication")
    assert current.fence == stale.fence + 1
    for operation in [lambda: store.guard(s.principal, stale), lambda: store.renew(s.principal, stale),
                      lambda: store.release(s.principal, stale), lambda: journal.prepare(s.principal, stale, review),
                      lambda: journal.advance(s.principal, stale, 1, "rejected", {"reason": "fixture"})]:
        with pytest.raises(ValueError, match="publication_lease_lost"):
            operation()
    assert journal.read(s.principal, "publication") == original
    store.guard(s.principal, current)


def test_payload_event_and_position_rollback_together(stored, monkeypatch):
    s = stored
    store, journal, _, review, _ = setup(s)
    lease = store.acquire(s.principal, "publication")
    original = journal._append
    def fail_after_write(*args):
        original(*args)
        raise RuntimeError("fixture rollback after actual event write")
    monkeypatch.setattr(journal, "_append", fail_after_write)
    with pytest.raises(RuntimeError, match="fixture rollback"):
        journal.prepare(s.principal, lease, review)
    state = journal.read(s.principal, "publication")
    assert state.payload is None and state.position == 0 and not state.events
    monkeypatch.setattr(journal, "_append", original)
    assert journal.prepare(s.principal, lease, review).position == 1


def test_db_clock_fence_is_rechecked_at_position_write(stored, monkeypatch):
    s = stored
    store, journal, _, review, _ = setup(s)
    lease = store.acquire(s.principal, "publication", 1)
    original = journal._append
    def expire_before_write(*args):
        time.sleep(1.1)
        return original(*args)
    monkeypatch.setattr(journal, "_append", expire_before_write)
    with pytest.raises(ValueError, match="publication_lease_or_position_lost"):
        journal.prepare(s.principal, lease, review)
    assert journal.read(s.principal, "publication").position == 0


def test_abandoned_upload_and_terminal_rejection_keep_prior_events(stored):
    s = stored
    store, journal, identity, review, artifact = setup(s)
    lease = store.acquire(s.principal, "publication")
    state = journal.prepare(s.principal, lease, review)
    first_id = state.attempt.identity.begin_id
    upload, _, _, _ = receipts(identity, artifact, state.attempt)
    for action, data in [("begun", upload.model_dump(mode="json")), ("streaming", None),
                         ("abandoned", None), ("replacement", None), ("rejected", {"reason": "rights_revoked"})]:
        state = journal.advance(s.principal, lease, state.position, action, data)
    assert state.attempt.identity.ordinal == 2 and state.attempt.identity.begin_id != first_id
    assert state.attempt.stage == "rejected" and len(state.events) == 6
    with pytest.raises(ValueError, match="publication_transition"):
        journal.advance(s.principal, lease, state.position, "replacement")
    assert journal.read(s.principal, "publication") == state


def test_actor_grants_unknown_trace_and_configuration_are_not_silently_changed(stored):
    s = stored
    store, journal, identity, review, _ = setup(s)
    wrong = replace(s.principal, actor_id="different")
    with pytest.raises(ValueError, match="publication_actor_binding"):
        journal.read(wrong, "publication")
    with pytest.raises(ValueError, match="publication_configuration_conflict"):
        PublicationStore(s.engine, "changed").register(s.principal, "publication", identity.trace())
    with pytest.raises(ValueError, match="publication_identity_conflict"):
        store.register(s.principal, "publication", identity.trace().model_copy(update={"sha256": "f" * 64}))
    with pytest.raises(ValueError, match="publication_trace_unknown"):
        store.register(s.principal, "other", identity.trace().model_copy(update={"trace_id": "absent"}))
    with pytest.raises(ValueError, match="publication_unknown"):
        store.acquire(s.principal, "missing")
    denied = replace(s.principal, actions=frozenset())
    with pytest.raises(PermissionError):
        journal.read(denied, "publication")
    with pytest.raises(PermissionError):
        store.acquire(denied, "publication")
    lease = store.acquire(s.principal, "publication")
    with pytest.raises(ValueError, match="publication_payload_pending"):
        journal.advance(s.principal, lease, 1, "streaming")
    for seconds in (0, 301, True):
        with pytest.raises(ValueError, match="publication_lease_seconds"):
            store.renew(s.principal, lease, seconds)
    assert journal.prepare(s.principal, lease, review).position == 1


def test_history_tables_are_insert_only_and_corrupt_events_fail_readback(stored):
    s = stored
    store, journal, _, review, _ = setup(s)
    lease = store.acquire(s.principal, "publication")
    state = journal.prepare(s.principal, lease, review)
    for table in ("trace_publications", "trace_publication_payloads", "trace_publication_events"):
        for sql in (f"UPDATE planning.{table} SET tenant_id=tenant_id WHERE false",
                    f"DELETE FROM planning.{table} WHERE false"):
            with pytest.raises(DBAPIError), s.engine.begin() as connection:
                connection.execute(text(sql))
    key = store.key(s.principal, "publication")
    with pytest.raises(ValueError, match="stored_publication_event_digest"), s.engine.begin() as connection:
        store.lock(connection, key)
        connection.execute(text("INSERT INTO planning.trace_publication_events "
            "(tenant_id,project_id,publication_id,position,event_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:publication,2,:digest,:content)"), {**key, "digest": "f" * 64, "content": b"{}"})
        connection.execute(text("UPDATE planning.trace_publication_control SET position=2 WHERE "
            "tenant_id=:tenant AND project_id=:project AND publication_id=:publication"), key)
        journal._read(connection, s.principal, key)
    assert journal.read(s.principal, "publication") == state  # Corruption probe rolled back.
