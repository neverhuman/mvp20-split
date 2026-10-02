from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_knowledge import ReasoningLimits
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.persistence.records import graph_key
from amphora_knowledge.reasoning.profile import RuleProfile
from amphora_knowledge.reasoning.workflow import ReasoningWorkflow
from amphora_knowledge.validation.transport import PeerUnavailable
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def test_durable_result_replays_without_evaluation_or_peers(reasoning_case, monkeypatch):
    c = reasoning_case
    result = c.workflow.submit(c.principal, c.request)
    assert result.decision.outcome == "evaluated"
    assert result.decision.result.findings[0].status == "supported"
    assert c.case.ledger.head(c.principal, c.request.snapshot.graph) == c.head
    assert c.workflow.read(c.principal, c.request.snapshot.graph, c.request.request_id) == result

    def forbidden(*args):
        raise AssertionError("terminal replay must not evaluate or read peers")

    monkeypatch.setattr(c.reviewer, "review_reasoning", forbidden)
    monkeypatch.setattr(RuleProfile, "evaluate", forbidden)
    replacement = ReasoningWorkflow(c.store, (), c.reviewer)
    assert replacement.submit(c.principal, c.request) == result


def test_outage_remains_pending_and_resumes_with_original_stored_profile(reasoning_case, monkeypatch):
    c = reasoning_case
    original = c.peer.content

    def outage(*args):
        assert c.workflow.read(c.principal, c.request.snapshot.graph, "reason").decision is None
        raise PeerUnavailable("peer_unavailable")

    monkeypatch.setattr(c.peer, "content", outage)
    with pytest.raises(PeerUnavailable):
        c.workflow.submit(c.principal, c.request)
    monkeypatch.setattr(c.peer, "content", original)
    replacement = ReasoningWorkflow(c.store, (), c.reviewer)
    result = replacement.submit(c.principal, c.request)
    assert result.decision.outcome == "evaluated" and result.request.rule_set == c.profile.reference


def test_rights_denial_is_a_stable_failed_decision(reasoning_case, monkeypatch):
    c = reasoning_case

    def denied(*args):
        raise KnowledgeError("peer_access_denied")

    monkeypatch.setattr(c.peer, "content", denied)
    result = c.workflow.submit(c.principal, c.request)
    assert result.decision.outcome == "failed" and result.decision.code == "peer_access_denied"
    assert c.workflow.submit(c.principal, c.request) == result


@pytest.mark.parametrize("variant", ["actor", "purpose"])
def test_identity_collision_cannot_rewrite_registered_intent(reasoning_case, variant):
    c = reasoning_case
    c.store.begin(c.principal, c.request, c.profile)
    principal, request = c.principal, c.request
    if variant == "actor":
        principal = replace(principal, actor_id="another")
    else:
        request = request.model_copy(update={"purpose": "changed"})
    with pytest.raises(KnowledgeError, match="reasoning_request_conflict"):
        c.workflow.submit(principal, request)


def test_wrong_snapshot_and_missing_profile_do_not_register_intent(reasoning_case):
    c = reasoning_case
    request = c.request.model_copy(update={"snapshot": c.request.snapshot.model_copy(update={"sha256": "0"*64})})
    with pytest.raises(KnowledgeError, match="reasoning_snapshot_unavailable"):
        c.store.begin(c.principal, request, c.profile)
    assert c.store.read(c.principal, c.request.snapshot.graph, "reason") is None
    with pytest.raises(KnowledgeError, match="reasoning_profile_unavailable"):
        c.store.begin(c.principal, c.request)


def test_rule_version_cannot_change_bytes_after_first_registration(reasoning_case):
    c = reasoning_case
    c.store.begin(c.principal, c.request, c.profile)
    profile = RuleProfile(c.profile.record.model_copy(update={"limits": ReasoningLimits(depth=1, work=100, facts=128)}))
    request = c.request.model_copy(update={"request_id": "other", "rule_set": profile.reference})
    with pytest.raises(KnowledgeError, match="reasoning_profile_identity_conflict"):
        c.store.begin(c.principal, request, profile)
    assert c.store.read(c.principal, c.request.snapshot.graph, "other") is None


def test_sql_interruption_preserves_pending_intent_and_original_snapshot(reasoning_case):
    c = reasoning_case

    def fault(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO knowledge.reasoning_decisions"):
            raise RuntimeError("simulated decision write interruption")

    event.listen(c.case.engine, "before_cursor_execute", fault)
    try:
        with pytest.raises(RuntimeError, match="interruption"):
            c.workflow.submit(c.principal, c.request)
    finally:
        event.remove(c.case.engine, "before_cursor_execute", fault)
    assert c.store.read(c.principal, c.request.snapshot.graph, "reason").decision is None
    assert c.case.ledger.head(c.principal, c.request.snapshot.graph) == c.head
    assert c.workflow.submit(c.principal, c.request).decision.outcome == "evaluated"


def test_duplicate_concurrent_evaluations_choose_one_immutable_result(reasoning_case, monkeypatch):
    c = reasoning_case
    barrier, original = Barrier(2), c.reviewer.review_reasoning

    def review(*args):
        result = original(*args)
        barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(c.reviewer, "review_reasoning", review)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(c.workflow.submit, c.principal, c.request) for _ in range(2)]
        outcomes = [future.result(timeout=20) for future in futures]
    assert outcomes[0] == outcomes[1] and outcomes[0].decision.outcome == "evaluated"


def test_scoped_reads_and_reasoning_grants_are_distinct(reasoning_case):
    c = reasoning_case
    reader = replace(c.principal, actions=frozenset({"read_graph"}))
    with pytest.raises(KnowledgeError, match="access_denied"):
        c.workflow.submit(reader, c.request)
    result = c.workflow.submit(c.principal, c.request)
    assert c.store.read(reader, c.request.snapshot.graph, "reason") == result
    foreign = c.request.snapshot.graph.model_copy(update={"graph_id": "other"})
    assert c.store.read(reader, foreign, "reason") is None


def test_owner_grants_deny_history_mutation(reasoning_case):
    c = reasoning_case
    c.workflow.submit(c.principal, c.request)
    for table in ("reasoning_profiles", "reasoning_intents", "reasoning_decisions"):
        with pytest.raises(DBAPIError) as error, c.case.engine.begin() as connection:
            connection.execute(text(f"DELETE FROM knowledge.{table} WHERE tenant_id=:tenant AND project_id=:project AND graph_id=:graph"),
                graph_key(c.request.snapshot.graph))
        assert error.value.orig.sqlstate == "42501"
