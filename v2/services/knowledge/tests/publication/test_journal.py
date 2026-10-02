from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_artifacts import DerivedUploadReceipt, UploadContentReceipt, UploadReceipt
from amphora_knowledge.authoring.canonical import KnowledgeError, canonical
from amphora_knowledge.publication.journal import PublicationJournal
from amphora_knowledge.publication.store import PUBLICATION_SCOPE, PublicationStore
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


@pytest.fixture
def journal_case(publication_case):
    c = publication_case
    c.document = c.publications.begin(c.principal, c.publication, c.publisher)
    c.lease = c.publications.acquire(c.principal, c.publication)
    c.journal = PublicationJournal(c.publications)
    c.observation = c.reviewer.review_reasoning(c.request, (c.peer.proposal.operations[2].assertion,))
    return c


def upload_for(progress):
    artifact = progress.payload.artifact
    return DerivedUploadReceipt(upload=UploadReceipt(upload_id=f"upload-{progress.attempt.identity.ordinal}",
        scope=artifact.result.request.snapshot.graph.scope, content=artifact.content), declaration=artifact.declaration)


def advance(c, progress, action, receipt=None):
    return c.journal.advance(c.lease, progress.position, action, receipt)


def streaming(c, progress):
    return advance(c, advance(c, progress, "begun", upload_for(progress)), "streaming")


def test_payload_and_command_identity_survive_store_replacement(journal_case):
    c = journal_case
    assert c.journal.read(c.principal, c.publication) is None
    first = c.journal.prepare(c.lease, c.observation)
    replacement = PublicationJournal(PublicationStore(c.case.engine))
    assert replacement.read(c.principal, c.publication) == first
    assert first.payload.artifact.body == canonical(first.payload.artifact.result)
    # Once persisted, retry returns the accepted payload rather than rewriting
    # its review timestamp or silently replacing its consumed input set.
    assert replacement.prepare(c.lease, c.observation.model_copy(update={"artifacts": ()})) == first
    assert first.publisher == c.publisher and first.position == 1
    assert first.attempt.begin_command(first.payload.artifact, c.publisher).identity.command_id == first.attempt.identity.begin_id


def test_initial_payload_and_first_event_commit_together(journal_case):
    c = journal_case

    def interrupt(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO knowledge.publication_events"):
            raise RuntimeError("event insertion interrupted")

    event.listen(c.case.engine, "before_cursor_execute", interrupt)
    try:
        with pytest.raises(RuntimeError, match="interrupted"):
            c.journal.prepare(c.lease, c.observation)
    finally:
        event.remove(c.case.engine, "before_cursor_execute", interrupt)
    assert c.journal.read(c.principal, c.publication) is None
    assert c.journal.prepare(c.lease, c.observation).position == 1


def test_ambiguous_stream_preserves_old_attempt_and_fences_late_reply(journal_case):
    c = journal_case
    first = c.journal.prepare(c.lease, c.observation)
    uncertain = streaming(c, first)
    stale = c.lease
    c.publications.release(stale)
    c.lease = c.publications.acquire(c.principal, c.publication)
    c.journal = PublicationJournal(PublicationStore(c.case.engine))
    assert c.journal.read(c.principal, c.publication) == uncertain
    with pytest.raises(KnowledgeError, match="publication_attempt_transition_invalid"):
        advance(c, uncertain, "finalizing")
    abandoned = advance(c, uncertain, "abandoned")
    replacement = advance(c, abandoned, "replacement")
    receipt = UploadContentReceipt(upload_id="upload-1", attempt_id="late", generation=1)
    with pytest.raises(KnowledgeError, match="publication_lease_lost"):
        c.journal.advance(stale, uncertain.position, "streamed", receipt)
    assert replacement.attempt.identity.ordinal == 2
    assert replacement.attempt.identity.begin_id != first.attempt.identity.begin_id
    with c.case.engine.connect() as connection:
        actions = connection.execute(text("SELECT action FROM knowledge.publication_events WHERE " + PUBLICATION_SCOPE +
            " ORDER BY position"), c.document.key).scalars().all()
    assert actions == ["prepared", "begun", "streaming", "abandoned", "prepared"]


def test_verified_stream_and_finalize_identity_survive_replacement(journal_case):
    c = journal_case
    progress = streaming(c, c.journal.prepare(c.lease, c.observation))
    progress = advance(c, progress, "streamed", UploadContentReceipt(upload_id="upload-1", attempt_id="stream-1", generation=1))
    progress = advance(c, progress, "finalizing")
    command = progress.attempt.finalize_command(c.publisher)
    c.journal = PublicationJournal(PublicationStore(c.case.engine))
    loaded = c.journal.read(c.principal, c.publication)
    assert loaded.attempt.finalize_command(c.publisher).canonical_bytes == command.canonical_bytes
    for action in ("abandoned", "replacement", "streaming"):
        with pytest.raises(KnowledgeError, match="publication_attempt_transition_invalid"):
            advance(c, loaded, action)
    assert c.journal.read(c.principal, c.publication) == loaded


def test_concurrent_writes_and_stale_positions_cannot_repeat_stream_start(journal_case):
    c = journal_case
    prepared = c.journal.prepare(c.lease, c.observation)
    begun = advance(c, prepared, "begun", upload_for(prepared))
    barrier = Barrier(2)

    def contender():
        barrier.wait(timeout=5)
        try:
            return advance(c, begun, "streaming")
        except KnowledgeError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(contender) for _ in range(2)]
        outcomes = [future.result(timeout=10) for future in futures]
    assert outcomes.count("publication_position_conflict") == 1
    assert c.journal.read(c.principal, c.publication).position == 3
    with pytest.raises(KnowledgeError, match="publication_position_conflict"):
        advance(c, begun, "streaming")


def test_eight_uncertain_uploads_are_retained_without_a_ninth(journal_case):
    c = journal_case
    progress = c.journal.prepare(c.lease, c.observation)
    for ordinal in range(1, 9):
        assert progress.attempt.identity.ordinal == ordinal
        progress = advance(c, streaming(c, progress), "abandoned")
        if ordinal < 8:
            progress = advance(c, progress, "replacement")
    with pytest.raises(KnowledgeError, match="publication_attempt_limit"):
        advance(c, progress, "replacement")
    restored = c.journal.read(c.principal, c.publication)
    assert restored.position == 32 and restored.attempt.stage == "abandoned"


def test_read_cannot_cross_original_actor_or_scope(journal_case):
    c = journal_case
    c.journal.prepare(c.lease, c.observation)
    with pytest.raises(KnowledgeError, match="publication_identity_conflict"):
        c.journal.read(replace(c.principal, actor_id="other"), c.publication)
    other = c.publication.model_copy(update={"graph": c.publication.graph.model_copy(update={
        "scope": c.publication.graph.scope.model_copy(update={"project_id": "other"})})})
    with pytest.raises(KnowledgeError, match="access_denied"):
        c.journal.read(c.principal, other)


def test_advance_without_reviewed_payload_cannot_record_an_attempt(journal_case):
    c = journal_case
    with pytest.raises(KnowledgeError, match="publication_payload_missing"):
        c.journal.advance(c.lease, 0, "streaming")


@pytest.mark.parametrize("table", ["publication_payloads", "publication_events"])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
def test_service_cannot_rewrite_or_delete_review_and_attempt_history(journal_case, table, verb):
    c = journal_case
    c.journal.prepare(c.lease, c.observation)
    command = f"UPDATE knowledge.{table} SET sha256=:sha" if verb == "UPDATE" else f"DELETE FROM knowledge.{table}"
    with pytest.raises(DBAPIError):
        with c.case.engine.begin() as connection:
            connection.execute(text(command + " WHERE " + PUBLICATION_SCOPE), c.document.key | {"sha": "0" * 64})


def test_corrupted_journal_digest_fails_closed(journal_case):
    c = journal_case
    c.journal.prepare(c.lease, c.observation)
    with c.case.engine.begin() as connection:
        connection.execute(text("INSERT INTO knowledge.publication_events "
            "(tenant_id,project_id,graph_id,publication_id,position,ordinal,action,canonical_bytes,sha256,fence,holder) "
            "VALUES (:tenant,:project,:graph,:publication,2,1,'begun',:body,:sha,1,'corrupt-fixture')"),
            c.document.key | {"body": b'{}', "sha": "0" * 64})
    with pytest.raises(KnowledgeError, match="publication_storage_mismatch"):
        c.journal.read(c.principal, c.publication)
