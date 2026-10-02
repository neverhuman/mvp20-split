"""Real PostgreSQL owner semantics; observation DTOs are declared synthetic fixtures."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from threading import Barrier

import pytest
from amphora_contracts_knowledge import ReferenceValidation, RetractAssertion
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.authoring.references import ReferencedInputs
from amphora_knowledge.persistence.ledger import KnowledgeLedger
from amphora_knowledge.persistence.records import SCOPE, graph_key
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def observation(proposal):
    refs = ReferencedInputs.collect(proposal)
    return ReferenceValidation(checked_at=datetime.now(UTC), artifacts=refs.artifacts, sources=refs.sources,
        conversion_traces=refs.traces, questions=refs.questions, evidence_needs=refs.needs)


def accept(e, proposal=None):
    proposal = proposal or e.proposal
    return e.ledger.accept(e.principal, proposal, observation(proposal))


def test_pending_intent_then_atomic_acceptance_and_exact_receipt_replay(stored_graph):
    e = stored_graph
    assert e.ledger.status(e.principal, e.proposal.graph, "first") is None
    pending = e.ledger.begin(e.principal, e.proposal)
    assert pending.decision is None and pending.proposal == e.proposal
    assert e.ledger.head(e.principal, e.proposal.graph) is None
    receipt = accept(e)
    assert receipt.decision.outcome == "accepted"
    head = receipt.decision.head
    assert e.ledger.head(e.principal, e.proposal.graph) == head
    assert e.ledger.snapshot(e.principal, head.snapshot).content.assertions[0].posture == "hypothesis"
    assert e.ledger.accept(e.principal, e.proposal, None) == receipt  # Completed replay performs no fresh validation.
    status = e.ledger.status(e.principal, e.proposal.graph, "first")
    assert status.decision == receipt and status.registered_at == pending.registered_at


def test_replacement_uses_persisted_profile_and_preserves_old_revision(stored_graph):
    e = stored_graph
    first = accept(e)
    old = e.ledger.snapshot(e.principal, first.decision.head.snapshot)
    claim = old.content.assertions[0]
    proposal = e.proposal.model_copy(update={"change_id": "retract", "base": first.decision.head,
        "operations": (RetractAssertion(operation="retract_assertion", assertion=claim.reference),)})
    replacement = KnowledgeLedger(e.engine, e.vocabulary, StructuralPolicy(max_entities=1))
    second = replacement.accept(e.principal, proposal, observation(proposal))
    assert second.decision.outcome == "accepted" and second.decision.head.snapshot.revision == 2
    assert replacement.snapshot(e.principal, first.decision.head.snapshot) == old
    rebuilt = replacement._load_state(proposal.graph)
    assert rebuilt.state.policy == e.policy  # New-graph defaults cannot silently change existing history.
    assert rebuilt.state.assertions.active() == ()
    assert replacement.accept(e.principal, e.proposal, None) == first


def test_changed_bytes_or_actor_cannot_reuse_pending_identity(stored_graph):
    e = stored_graph
    e.ledger.begin(e.principal, e.proposal)
    with pytest.raises(KnowledgeError, match="proposal_identity_conflict"):
        e.ledger.begin(e.principal, e.proposal.model_copy(update={"description": "changed"}))
    with pytest.raises(KnowledgeError, match="proposal_actor_conflict"):
        e.ledger.begin(replace(e.principal, actor_id="different"), e.proposal)
    assert e.ledger.status(e.principal, e.proposal.graph, "first").decision is None


def test_rejected_and_stale_proposals_stay_auditable_without_entering_replay(stored_graph):
    e = stored_graph
    claim = e.proposal.operations[2].assertion.model_copy(update={"predicate": "unknown"})
    invalid = e.proposal.model_copy(update={"change_id": "invalid", "operations": (
        *e.proposal.operations[:2], e.proposal.operations[2].model_copy(update={"assertion": claim}))})
    rejected = accept(e, invalid)
    assert rejected.decision.outcome == "rejected" and rejected.decision.findings[0].code == "unknown_predicate"
    assert e.ledger.head(e.principal, e.proposal.graph) is None
    first = accept(e)
    stale = e.proposal.model_copy(update={"change_id": "stale"})
    conflict = accept(e, stale)
    assert conflict.decision.outcome == "conflict"
    assert e.ledger.head(e.principal, e.proposal.graph) == first.decision.head
    assert e.ledger.accept(e.principal, invalid, None) == rejected
    with e.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM knowledge.accepted_changes WHERE " + SCOPE), graph_key(e.proposal.graph)).scalar_one() == 1


def test_two_prepared_writers_at_same_base_get_one_accept_and_one_conflict(stored_graph, monkeypatch):
    e = stored_graph
    barrier = Barrier(2)
    original = e.ledger._load_state

    def capture(graph):
        state = original(graph)
        barrier.wait(timeout=10)
        return state

    monkeypatch.setattr(e.ledger, "_load_state", capture)
    proposals = [e.proposal.model_copy(update={"change_id": identity}) for identity in ("left", "right")]
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda p: accept(e, p), proposals))
    assert sorted(r.decision.outcome for r in receipts) == ["accepted", "conflict"]
    assert e.ledger.head(e.principal, e.proposal.graph).snapshot.revision == 1
    assert all(e.ledger.status(e.principal, e.proposal.graph, p.change_id).decision == r for p, r in zip(proposals, receipts, strict=True))


def test_concurrent_exact_delivery_returns_one_committed_receipt(stored_graph, monkeypatch):
    e = stored_graph
    barrier = Barrier(2)
    original = e.ledger._load_state

    def capture(graph):
        state = original(graph)
        barrier.wait(timeout=10)
        return state

    monkeypatch.setattr(e.ledger, "_load_state", capture)
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda _value: accept(e), range(2)))
    assert receipts[0] == receipts[1] and receipts[0].decision.outcome == "accepted"
    with e.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM knowledge.accepted_changes WHERE " + SCOPE), graph_key(e.proposal.graph)).scalar_one() == 1


def test_failure_after_head_write_rolls_back_all_acceptance_but_keeps_intent(stored_graph):
    e = stored_graph

    def fail(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO knowledge.decisions "):
            raise RuntimeError("test acceptance barrier")

    event.listen(e.engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="test acceptance barrier"):
            accept(e)
    finally:
        event.remove(e.engine, "before_cursor_execute", fail)
    assert e.ledger.head(e.principal, e.proposal.graph) is None
    assert e.ledger.status(e.principal, e.proposal.graph, "first").decision is None
    with e.engine.connect() as connection:
        for table in ("accepted_changes", "snapshots", "heads", "decisions"):
            assert connection.execute(text(f"SELECT count(*) FROM knowledge.{table} WHERE " + SCOPE), graph_key(e.proposal.graph)).scalar_one() == 0
    assert accept(e).decision.outcome == "accepted"


def test_scope_grants_and_immutable_history_are_owner_enforced(stored_graph):
    e = stored_graph
    with pytest.raises(KnowledgeError, match="access_denied"):
        e.ledger.begin(replace(e.principal, actions=frozenset({"read_graph"})), e.proposal)
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "foreign"}))
    with pytest.raises(KnowledgeError, match="access_denied"):
        e.ledger.begin(foreign, e.proposal)
    receipt = accept(e)
    with pytest.raises(KnowledgeError, match="access_denied"):
        e.ledger.snapshot(foreign, receipt.decision.head.snapshot)
    for statement in ["UPDATE knowledge.proposals SET actor_id=actor_id", "DELETE FROM knowledge.accepted_changes",
                      "UPDATE knowledge.snapshots SET snapshot_sha256=snapshot_sha256", "DELETE FROM knowledge.decisions",
                      "UPDATE knowledge.graph_profiles SET policy_bytes=policy_bytes"]:
        with e.engine.connect() as connection:
            try:
                with pytest.raises(DBAPIError) as denied:
                    connection.execute(text(statement + " WHERE " + SCOPE), graph_key(e.proposal.graph))
                assert denied.value.orig.sqlstate == "42501"
            finally:
                connection.rollback()
    with pytest.raises(DBAPIError) as denied, e.engine.begin() as connection:
        connection.execute(text("SELECT 1 FROM artifacts.catalog LIMIT 0"))
    assert denied.value.orig.sqlstate == "42501"


def test_accepted_snapshot_pair_cannot_commit_half_a_record(stored_graph):
    e = stored_graph
    e.ledger.begin(e.principal, e.proposal)
    with pytest.raises(DBAPIError) as missing, e.engine.begin() as connection:
        connection.execute(text("INSERT INTO knowledge.accepted_changes "
            "(tenant_id,project_id,graph_id,position,prior_position,change_id,change_sha256,snapshot_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:graph,1,NULL,'first',:sha,:sha,:body)"),
            graph_key(e.proposal.graph) | {"sha": "a"*64, "body": b"{}"})
    assert missing.value.orig.sqlstate == "23503"
    assert e.ledger.head(e.principal, e.proposal.graph) is None


def test_missing_predecessor_cannot_exploit_nullable_sql_check(stored_graph):
    e = stored_graph
    e.ledger.begin(e.principal, e.proposal)
    with pytest.raises(DBAPIError) as rejected, e.engine.begin() as connection:
        connection.execute(text("INSERT INTO knowledge.accepted_changes "
            "(tenant_id,project_id,graph_id,position,prior_position,change_id,change_sha256,snapshot_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:graph,2,NULL,'first',:sha,:sha,:body)"),
            graph_key(e.proposal.graph) | {"sha": "a"*64, "body": b"{}"})
    assert rejected.value.orig.sqlstate == "23514"


def test_terminal_rejection_replays_and_missing_snapshot_is_not_fabricated(stored_graph):
    e = stored_graph
    first = accept(e)
    missing = first.decision.head.snapshot.model_copy(update={"sha256": "0"*64})
    assert e.ledger.snapshot(e.principal, missing) is None
    other = e.proposal.model_copy(update={"change_id": "rejected"})
    rejected = e.ledger.reject(e.principal, other, "unresolved_reference")
    assert e.ledger.reject(e.principal, other, "different_reason") == rejected
