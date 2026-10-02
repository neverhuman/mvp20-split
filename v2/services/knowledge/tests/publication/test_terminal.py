from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_contracts_artifacts import (
    DerivationReceipt,
    FinalizedReceipt,
    PublicationObservation,
    UploadContentReceipt,
)
from amphora_contracts_core import ArtifactRef
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.publication.journal import PublicationJournal
from amphora_knowledge.publication.store import PUBLICATION_SCOPE, PublicationStore
from amphora_knowledge.publication.terminal import PublicationTerminals
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from .test_journal import advance, streaming

pytestmark = pytest.mark.postgres


@pytest.fixture
def terminal_case(journal_case):
    c = journal_case
    c.terminals = PublicationTerminals(c.journal)
    progress = streaming(c, c.journal.prepare(c.lease, c.observation))
    progress = advance(c, progress, "streamed", UploadContentReceipt(upload_id="upload-1", attempt_id="stream-1", generation=1))
    c.progress = advance(c, progress, "finalizing")
    artifact = c.progress.payload.artifact
    ref = ArtifactRef(artifact_id="published-result", scope=c.publication.graph.scope, **artifact.content.model_dump())
    c.finalized = FinalizedReceipt(upload_id="upload-1", artifact=ref)
    command = c.progress.attempt.begin_command(artifact, c.publisher)
    c.derivation = DerivationReceipt(origin=command.identity, request_sha256=command.sha256, upload_id="upload-1",
        artifact=ref, declaration=artifact.declaration)
    return c


def finish(c):
    return c.terminals.finish(c.lease, c.progress.position, c.finalized, c.derivation)


def test_terminal_pairs_artifact_and_receipt_with_bounded_authority(terminal_case):
    c = terminal_case
    assert c.terminals.read(c.principal, c.publication).outcome.status == "pending"
    status = finish(c)
    assert status.outcome.status == "published"
    assert status.outcome.derivation == c.derivation
    receipt = status.outcome.receipt
    assert receipt.purpose == "knowledge.synthetic_entailment" and receipt.purpose != c.request.purpose
    assert receipt.subject == c.request.subject and receipt.issuer_id == c.publisher.issuer_id
    assert receipt.outcome.status == "accepted"
    assert receipt.outcome.output.artifact == c.finalized.artifact
    assert receipt.outcome.output.representation == "knowledge.reasoning_result.v1"
    assert receipt.outcome.output.unit == "1"
    replacement = PublicationTerminals(PublicationJournal(PublicationStore(c.case.engine)))
    assert replacement.read(c.principal, c.publication) == status
    assert replacement.finish(c.lease, -1, None, None) == status
    with pytest.raises(KnowledgeError, match="publication_already_terminal"):
        c.journal.advance(c.lease, c.progress.position, "abandoned")


def test_interrupted_terminal_insert_exposes_neither_artifact_nor_receipt(terminal_case):
    c = terminal_case

    def interrupt(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO knowledge.publication_terminals"):
            raise RuntimeError("terminal insertion interrupted")

    event.listen(c.case.engine, "before_cursor_execute", interrupt)
    try:
        with pytest.raises(RuntimeError, match="interrupted"):
            finish(c)
    finally:
        event.remove(c.case.engine, "before_cursor_execute", interrupt)
    assert c.terminals.read(c.principal, c.publication).outcome.status == "pending"
    assert c.journal.read(c.principal, c.publication) == c.progress
    assert finish(c).outcome.status == "published"


def test_concurrent_terminal_replays_choose_one_receipt(terminal_case):
    c = terminal_case
    barrier = Barrier(2)

    def contender():
        barrier.wait(timeout=5)
        return finish(c)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(contender) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert results[0] == results[1]
    assert c.terminals.read(c.principal, c.publication) == results[0]


def test_unknown_finalization_cannot_be_declared_failed(terminal_case):
    c = terminal_case
    with pytest.raises(KnowledgeError, match="publication_finalization_unresolved"):
        c.terminals.fail(c.lease, c.progress.position, "peer_unavailable")
    assert c.terminals.read(c.principal, c.publication).outcome.status == "pending"


def test_bound_rejected_finalize_can_be_failed_without_hiding_prior_effects(terminal_case):
    c = terminal_case
    command = c.progress.attempt.finalize_command(c.publisher)
    proof = PublicationObservation.model_validate({"identity": command.identity, "operation_id": "op",
        "request_sha256": command.sha256, "outcome": {"status": "rejected", "reason_code": "rights_revoked"}})
    with pytest.raises(KnowledgeError, match="publication_rejection_mismatch"):
        c.terminals.fail(c.lease, c.progress.position, "rights_revoked", rejection=proof.model_copy(update={"request_sha256": "0" * 64}))
    status = c.terminals.fail(c.lease, c.progress.position, "rights_revoked", rejection=proof)
    assert status.outcome.status == "failed" and status.outcome.external_effects == "possible"
    assert c.terminals.read(c.principal, c.publication) == status
    assert finish(c) == status


@pytest.mark.parametrize("prepared", [False, True])
def test_failure_effects_come_from_retained_progress(journal_case, prepared):
    c = journal_case
    terminals = PublicationTerminals(c.journal)
    position = c.journal.prepare(c.lease, c.observation).position if prepared else None
    status = terminals.fail(c.lease, position, "provenance_denied")
    assert status.outcome.external_effects == ("possible" if prepared else "none")
    assert terminals.read(c.principal, c.publication) == status
    with pytest.raises(KnowledgeError, match="publication_already_terminal"):
        c.journal.prepare(c.lease, c.observation)


def test_stale_position_and_lease_cannot_commit_terminal(terminal_case):
    c = terminal_case
    with pytest.raises(KnowledgeError, match="publication_position_conflict"):
        c.terminals.finish(c.lease, c.progress.position - 1, c.finalized, c.derivation)
    with pytest.raises(KnowledgeError, match="publication_position_conflict"):
        c.terminals.fail(c.lease, c.progress.position - 1, "stale_error")
    c.publications.release(c.lease)
    with pytest.raises(KnowledgeError, match="publication_lease_lost"):
        finish(c)


@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
def test_terminal_records_cannot_be_rewritten(terminal_case, verb):
    c = terminal_case
    finish(c)
    command = "UPDATE knowledge.publication_terminals SET sha256=:sha" if verb == "UPDATE" else "DELETE FROM knowledge.publication_terminals"
    with pytest.raises(DBAPIError):
        with c.case.engine.begin() as connection:
            connection.execute(text(command + " WHERE " + PUBLICATION_SCOPE), c.document.key | {"sha": "0" * 64})
