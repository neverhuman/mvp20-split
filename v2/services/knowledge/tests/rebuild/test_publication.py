"""Actual PostgreSQL publication/CAS; no peer observations are inferred here."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_knowledge import ReviseEntityContext
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.rebuild.model import Candidate
from amphora_knowledge.rebuild.store import RebuildStore
from amphora_knowledge.rebuild.workflow import RebuildWorkflow
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

from ..persistence.test_ledger import observation

pytestmark = pytest.mark.postgres


@pytest.fixture
def rebuild(stored_graph):
    case = stored_graph
    case.principal = replace(case.principal, actions=case.principal.actions | {"rebuild_graph"})
    case.receipt = case.ledger.accept(case.principal, case.proposal, observation(case.proposal))
    case.store = RebuildStore(case.engine)
    case.workflow = RebuildWorkflow(case.store)
    return case


def advance(case, name):
    state = case.ledger._load_state(case.proposal.graph)
    original = state.state.entities.records[-1]
    replacement = original.model_copy(update={"reference": original.reference.model_copy(update={
        "revision": original.reference.revision + 1}), "supersedes": original.reference})
    proposal = case.proposal.model_copy(update={"change_id": name, "base": state.head,
        "operations": (ReviseEntityContext(operation="revise_entity_context", prior=original.reference,
                                           replacement=replacement),)})
    result = case.ledger.accept(case.principal, proposal, observation(proposal))
    assert result.decision.outcome == "accepted"
    return result.decision.head


def test_rebuild_publishes_same_semantics_and_exact_retry(rebuild, monkeypatch):
    case = rebuild
    graph = case.proposal.graph
    head = case.receipt.decision.head
    before = case.ledger.snapshot(case.principal, head.snapshot)
    result = case.workflow.run(case.principal, graph, "first")
    assert result.outcome == "published" and result.result_head == head and result.attempts == 1
    assert case.ledger.head(case.principal, graph) == head
    assert case.ledger.snapshot(case.principal, head.snapshot) == before
    assert case.store.status(case.principal, graph, "first") == result
    monkeypatch.setattr(case.workflow.history, "cursor", lambda *args: pytest.fail("terminal rebuild replayed"))
    assert case.workflow.run(case.principal, graph, "first") == result


def test_stale_first_candidate_catches_up_exact_tail(rebuild, monkeypatch):
    case = rebuild
    publish, tail = case.store.publish, case.workflow.history.tail
    tails = []

    def racing(candidate):
        if candidate.attempt == 1:
            advance(case, "racing-edit")
        return publish(candidate)

    def tracked(graph, after, watermark):
        tails.append((after, watermark.change.position))
        return tail(graph, after, watermark)

    monkeypatch.setattr(case.store, "publish", racing)
    monkeypatch.setattr(case.workflow.history, "tail", tracked)
    result = case.workflow.run(case.principal, case.proposal.graph, "catch-up")
    assert result.outcome == "published" and result.attempts == 2
    assert tails == [(0, 1), (1, 2)]
    assert result.result_head == case.ledger.head(case.principal, case.proposal.graph)


def test_continuous_edits_defer_without_regressing_or_hiding_head(rebuild, monkeypatch):
    case = rebuild
    publish = case.store.publish
    previous = case.workflow.run(case.principal, case.proposal.graph, "prior")

    def racing(candidate):
        advance(case, "edit-" + str(candidate.attempt))
        return publish(candidate)

    monkeypatch.setattr(case.store, "publish", racing)
    result = case.workflow.run(case.principal, case.proposal.graph, "contended")
    assert result.outcome == "deferred" and result.attempts == 3
    head = case.ledger.head(case.principal, case.proposal.graph)
    assert head.change.position == 4
    assert case.ledger.snapshot(case.principal, head.snapshot).reference == head.snapshot
    assert case.ledger.snapshot(case.principal, previous.result_head.snapshot) is not None
    with case.engine.connect() as connection:
        pointer = connection.execute(text("SELECT rebuild_id FROM knowledge.snapshot_publications WHERE project_id=:project"),
            {"project": case.principal.scope.project_id}).scalar_one()
    assert pointer == "prior"


def test_failure_after_pointer_write_rolls_back_and_preserves_pending(rebuild):
    case = rebuild
    head = case.receipt.decision.head

    def fail(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO knowledge.rebuild_results"):
            raise RuntimeError("injected_publication_failure")

    event.listen(case.engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            case.workflow.run(case.principal, case.proposal.graph, "retry")
    finally:
        event.remove(case.engine, "before_cursor_execute", fail)
    assert case.store.status(case.principal, case.proposal.graph, "retry").outcome == "pending"
    assert case.ledger.snapshot(case.principal, head.snapshot).reference == head.snapshot
    with case.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM knowledge.snapshot_publications WHERE project_id=:project"),
            {"project": case.principal.scope.project_id}).scalar_one() == 0
    assert case.workflow.run(case.principal, case.proposal.graph, "retry").outcome == "published"


def test_duplicate_concurrent_builds_converge_on_one_result(rebuild, monkeypatch):
    case = rebuild
    barrier, stage = Barrier(2), case.store.stage

    def staged(candidate):
        stage(candidate)
        barrier.wait(timeout=10)

    monkeypatch.setattr(case.store, "stage", staged)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(case.workflow.run, case.principal, case.proposal.graph, "duplicate") for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert results[0] == results[1] and results[0].outcome == "published"


def test_bad_history_fails_without_publication(rebuild, monkeypatch):
    case = rebuild
    monkeypatch.setattr(case.workflow.history, "tail", lambda *args: iter(()))
    result = case.workflow.run(case.principal, case.proposal.graph, "missing-tail")
    assert result.outcome == "failed" and result.code == "replay_watermark_mismatch"
    assert case.ledger.head(case.principal, case.proposal.graph) == case.receipt.decision.head


def test_candidate_stays_private_until_cas_publication(rebuild):
    case = rebuild
    started = case.store.begin(case.principal, case.proposal.graph, "staged")
    cursor = case.workflow.history.cursor(case.proposal.graph).through(
        case.workflow.history.tail(case.proposal.graph, 0, started.initial_head), started.initial_head)
    candidate = Candidate.from_cursor(started.request, 1, cursor)
    case.store.stage(candidate)
    advanced = advance(case, "new-head")
    assert case.store.publish(candidate) is None
    assert case.store.status(case.principal, case.proposal.graph, "staged").outcome == "pending"
    assert case.ledger.snapshot(case.principal, advanced.snapshot).reference == advanced.snapshot


def test_actions_scope_actor_and_unknown_graph(rebuild):
    case = rebuild
    reader = replace(case.principal, actions=frozenset({"read_graph"}))
    with pytest.raises(KnowledgeError, match="access_denied"):
        case.workflow.run(reader, case.proposal.graph, "forbidden")
    foreign = case.proposal.graph.model_copy(update={"scope": case.principal.scope.model_copy(update={"project_id": "other"})})
    with pytest.raises(KnowledgeError, match="access_denied"):
        case.store.status(case.principal, foreign, "foreign")
    assert case.store.status(reader, case.proposal.graph, "unknown") is None
    case.store.begin(case.principal, case.proposal.graph, "actor")
    with pytest.raises(KnowledgeError, match="rebuild_actor_conflict"):
        case.store.begin(replace(case.principal, actor_id="another"), case.proposal.graph, "actor")
    missing = case.proposal.graph.model_copy(update={"graph_id": "missing"})
    with pytest.raises(KnowledgeError, match="rebuild_graph_unavailable"):
        case.store.begin(case.principal, missing, "missing")


def test_database_forbids_unbacked_pointer_and_history_mutation(rebuild):
    case = rebuild
    started = case.store.begin(case.principal, case.proposal.graph, "unpublished")
    cursor = case.workflow.history.cursor(case.proposal.graph).through(
        case.workflow.history.tail(case.proposal.graph, 0, started.initial_head), started.initial_head)
    candidate = Candidate.from_cursor(started.request, 1, cursor)
    case.store.stage(candidate)
    with pytest.raises(DBAPIError) as error:
        with case.engine.begin() as connection:
            connection.execute(text("INSERT INTO knowledge.snapshot_publications "
                "(tenant_id,project_id,graph_id,rebuild_id,candidate_id) VALUES (:tenant,:project,:graph,:rebuild,:candidate)"), candidate.bindings)
    assert error.value.orig.sqlstate == "23503"
    for table in ("rebuild_intents", "rebuild_candidates", "rebuild_results"):
        with case.engine.connect() as connection:
            transaction = connection.begin()
            try:
                with pytest.raises(DBAPIError) as error:
                    connection.execute(text(f"DELETE FROM knowledge.{table} WHERE project_id=:project"),
                        {"project": case.principal.scope.project_id})
                assert error.value.orig.sqlstate == "42501"
            finally:
                transaction.rollback()
