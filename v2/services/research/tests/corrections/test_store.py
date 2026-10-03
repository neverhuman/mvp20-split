"""Real owner PostgreSQL transactions; source publications use explicit synthetic terminal fixtures."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_graph_runtime import ReceiptChainRef
from amphora_contracts_research import CorrectAssessmentReceipt, SelectAssessmentReceipt
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.resolution import ResolvedAssessment
from amphora_research.corrections.store import CorrectionStore
from amphora_research.publication.store import PublicationStore
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from ..publication.test_publication import stream_to_finalize, terminal

pytestmark = pytest.mark.postgres


@pytest.fixture
def correction_case(assessment_store):
    owner, bound, resolved = assessment_store

    def published(name):
        selected = replace(bound, request=bound.request.model_copy(update={"assessment_id":name}))
        owner.begin(selected)
        owner.complete(selected, ResolvedAssessment(selected.evaluate((), ()), resolved.inputs))
        publications = PublicationStore(owner.engine)
        initial = publications.begin(selected.request.profile.scope, name, selected.actor_id, "publisher", "issuer")
        lease = publications.acquire(initial)
        progress = stream_to_finalize(publications, lease)
        result = publications.advance(lease, progress.position, "published", terminal(progress))
        publications.release(lease)
        return result.receipt

    for name in ("first", "second", "third"):
        published(name)
    chain = ReceiptChainRef(scope=bound.request.profile.scope, issuer_id="issuer", chain_id="chain")
    request = CorrectAssessmentReceipt(wire_version="1", chain=chain, change_id="create",
        assessment_id="first", reason_code="initial", expected_head=None)
    return CorrectionStore(owner.engine), request, bound.actor_id


def test_immutable_replay_history_and_explicit_head_selection(correction_case):
    store, request, actor = correction_case
    first = store.append(request, actor)
    successor = request.model_copy(update={"change_id":"correction", "assessment_id":"second", "expected_head":first.reference})
    second = store.append(successor, actor)
    replacement = CorrectionStore(store.engine)
    assert replacement.append(request, actor) == first
    assert replacement.append(successor, actor) == second
    query = SelectAssessmentReceipt(wire_version="1", chain=request.chain, revision=None)
    assert replacement.select(query) == second
    assert replacement.select(query.model_copy(update={"revision":first.reference})) == first
    assert second.record.notice.revision == first.record.receipt.revision
    original = PublicationStore(store.engine).lookup(request.chain.scope, "first", actor).receipt
    assert original == first.record.source_receipt
    assert original.revision == "1" and original.outcome.status == "abstained"
    with pytest.raises(AssessmentError, match="selection_conflict"):
        replacement.select(query.model_copy(update={"revision":first.reference.model_copy(update={"record_sha256":"a"*64})}))
    with pytest.raises(AssessmentError, match="identity_conflict"):
        replacement.append(request.model_copy(update={"reason_code":"changed"}), actor)
    with pytest.raises(AssessmentError, match="actor_mismatch"):
        replacement.append(request, "another")
    with store.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text("UPDATE research.receipt_corrections SET ordinal=ordinal"))


def test_competing_successors_commit_one_head(correction_case):
    store, request, actor = correction_case
    first = store.append(request, actor)
    barrier = Barrier(2)

    def submit(name):
        command = request.model_copy(update={"change_id":name, "assessment_id":name, "expected_head":first.reference})
        barrier.wait(timeout=10)
        try:
            return store.append(command, actor).record.ordinal
        except AssessmentError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, ("second", "third")))
    assert sorted(results, key=str) == [2, "correction_head_conflict"]
    assert store.select(SelectAssessmentReceipt(wire_version="1", chain=request.chain, revision=None)).record.ordinal == 2


def test_failed_commit_rolls_back_record_and_head(correction_case):
    store, request, actor = correction_case

    def fail(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO research.receipt_corrections"):
            raise RuntimeError("injected_after_insert")

    event.listen(store.engine, "after_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected_after_insert"):
            store.append(request, actor)
    finally:
        event.remove(store.engine, "after_cursor_execute", fail)
    assert store.select(SelectAssessmentReceipt(wire_version="1", chain=request.chain, revision=None)) is None
    assert store.append(request, actor).record.ordinal == 1


def test_missing_source_and_foreign_scope_never_create_correction(correction_case):
    store, request, actor = correction_case
    with pytest.raises(AssessmentError, match="publication_pending"):
        store.append(request.model_copy(update={"assessment_id":"missing"}), actor)
    foreign = request.chain.model_copy(update={"scope":request.chain.scope.model_copy(update={"project_id":"foreign"})})
    assert store.select(SelectAssessmentReceipt(wire_version="1", chain=foreign, revision=None)) is None
    with pytest.raises(AssessmentError, match="publication_pending"):
        store.append(request.model_copy(update={"chain":foreign}), actor)


def test_concurrent_same_change_is_one_exact_replay(correction_case):
    store, request, actor = correction_case
    barrier = Barrier(2)

    def submit(_):
        barrier.wait(timeout=10)
        return store.append(request, actor)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert results[0] == results[1]
    assert results[0].record.ordinal == 1
    with store.engine.connect() as connection:
        count = connection.execute(text("SELECT count(*) FROM research.receipt_corrections "
            "WHERE tenant_id=:tenant AND project_id=:project AND issuer_id=:issuer AND chain_id=:chain"),
            store._key(request.chain)).scalar_one()
    assert count == 1


def test_selection_and_expected_head_cannot_cross_chain(correction_case):
    store, request, actor = correction_case
    first = store.append(request, actor)
    other = first.reference.model_copy(update={"chain":request.chain.model_copy(update={"chain_id":"other"})})
    with pytest.raises(AssessmentError, match="selection_mismatch"):
        store.select(SelectAssessmentReceipt(wire_version="1", chain=request.chain, revision=other))
    with pytest.raises(AssessmentError, match="predecessor_mismatch"):
        store.append(request.model_copy(update={"change_id":"next", "expected_head":other}), actor)
