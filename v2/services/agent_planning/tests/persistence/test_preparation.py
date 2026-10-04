"""Owned SQL preparation proofs; peer records here are scripted public fixtures."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.dispatch import DispatchJournal
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.persistence.preparation import PreparationJournal
from amphora_agent_planning.persistence.repair import RepairJournal
from amphora_agent_planning.persistence.settlement import SettlementJournal
from amphora_agent_planning.repair.history import RepairHistory
from amphora_agent_planning.repair.preparation import RepairPreparer
from amphora_agent_planning.repair.prompt import RepairPrompt
from amphora_agent_planning.research_proposals.context import QuestionContext
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from ..repair.test_preparation import setup

pytestmark = pytest.mark.postgres


def enrolled(s, *, selected_question=False, enroll_child=True, return_fixture=False, root_only=False, abstain=False):
    history, feedback, interpretation, data, knowledge = setup(scope=s.principal.scope, selected_question=selected_question, abstain=abstain)
    traces, families = ExtractionJournal(s.engine), RepairJournal(s.engine)
    task = history.task
    s.journal.register(s.principal, task.request)
    traces.register(s.principal, task)
    families.enroll_root(s.principal, task.document().task_id, history.root.policy)
    binding = AttemptBinding(task.request, 1)
    BudgetLedger(s.engine).reserve(s.principal, binding, history.root.policy)
    s.journal.record(s.principal, binding, history.observation)
    SettlementJournal(s.engine).settle(s.principal, binding)
    parent = traces.record(s.principal, task.document().task_id, binding.reference(), history.projection.reference().trace_id)
    actual = RepairHistory.read(s.engine, s.principal, task.document().engagement, parent.projection.reference())
    assert actual == history
    if root_only:
        return actual, feedback, interpretation, data, knowledge
    prepared = RepairPreparer(data, knowledge).prepare(actual, feedback, interpretation)
    child = prepared.plan.task
    s.journal.register(s.principal, child.request)
    traces.register(s.principal, child)
    if enroll_child:
        families.enroll_child(s.principal, task.document().engagement, child.document().task_id, parent.projection.reference())
    return (prepared, data, knowledge) if return_fixture else prepared


def test_preparation_exact_replay_concurrent_writers_and_replacement(stored):
    s = stored
    prepared = enrolled(s)
    gate = Barrier(2)
    def write(_):
        gate.wait(timeout=5)
        return PreparationJournal(s.engine).register(s.principal, prepared)
    with ThreadPoolExecutor(2) as workers:
        left, right = list(workers.map(write, range(2)))
    assert left == right
    engine = create_engine(s.engine.url)
    try:
        replacement = PreparationJournal(engine)
        assert replacement.read(s.principal, prepared.plan.task.document().engagement) == left
        assert replacement.register(s.principal, prepared) == left
    finally:
        engine.dispose()
    for statement in ("DELETE FROM planning.repair_preparations WHERE false",
                      "UPDATE planning.repair_preparations SET packet_sha256=packet_sha256 WHERE false"):
        with pytest.raises(DBAPIError) as caught, s.engine.begin() as connection:
            connection.execute(text(statement))
        assert caught.value.orig.sqlstate == "42501"


def test_changed_availability_cannot_replace_first_preparation(stored):
    s = stored
    prepared = enrolled(s, selected_question=True)
    journal = PreparationJournal(s.engine)
    first = journal.register(s.principal, prepared)
    gap = prepared.questions.unavailable()[0]
    questions = QuestionContext.bind(prepared.plan.task, (), ((gap[0], "research_access_denied"),))
    changed = replace(prepared, questions=questions,
        packet=RepairPrompt.render(prepared.plan, prepared.sources, prepared.knowledge, questions))
    with pytest.raises(ValueError, match="repair_preparation_conflict"):
        journal.register(s.principal, changed)
    assert journal.read(s.principal, prepared.plan.task.document().engagement) == first


def test_missing_membership_rejected_without_record(stored):
    s = stored
    prepared = enrolled(s, enroll_child=False)
    journal = PreparationJournal(s.engine)
    with pytest.raises(ValueError, match="repair_preparation_membership"):
        journal.register(s.principal, prepared)
    assert journal.read(s.principal, prepared.plan.task.document().engagement) is None


@pytest.mark.parametrize("consumed", ["issued", "observed"])
def test_first_attestation_after_a_call_is_rejected(stored, consumed):
    s = stored
    prepared = enrolled(s)
    bound = AttemptBinding(prepared.plan.task.request, 1)
    BudgetLedger(s.engine).reserve(s.principal, bound, prepared.history.root.policy)
    journal = PreparationJournal(s.engine)
    assert not journal.issued(s.principal, bound)
    if consumed == "issued":
        DispatchJournal(s.engine).issue(s.principal, bound, 10)
        assert journal.issued(s.principal, bound)
    else:
        from amphora_agent_planning.providers import observe

        from .test_extraction import Response
        s.journal.record(s.principal, bound, observe(bound, Response(b"{")))
    with pytest.raises(ValueError, match="repair_preparation_after_call"):
        journal.register(s.principal, prepared)
    assert journal.read(s.principal, bound.reference().engagement) is None


def test_unissued_reservation_allows_preparation_and_later_exact_replay(stored):
    s = stored
    prepared = enrolled(s)
    bound = AttemptBinding(prepared.plan.task.request, 1)
    BudgetLedger(s.engine).reserve(s.principal, bound, prepared.history.root.policy)
    journal = PreparationJournal(s.engine)
    first = journal.register(s.principal, prepared)
    DispatchJournal(s.engine).issue(s.principal, bound, 10)
    assert journal.register(s.principal, prepared) == first


def test_preparation_actor_scope_and_permission_are_owned(stored):
    s = stored
    prepared = enrolled(s)
    journal = PreparationJournal(s.engine)
    first = journal.register(s.principal, prepared)
    with pytest.raises(ValueError, match="actor"):
        journal.register(replace(s.principal, actor_id="other"), prepared)
    with pytest.raises(PermissionError, match="planning_access_denied"):
        journal.read(replace(s.principal, scope=s.principal.scope.model_copy(update={"project_id": "other"})),
                     prepared.plan.task.document().engagement)
    with pytest.raises(PermissionError, match="planning_access_denied"):
        journal.register(replace(s.principal, actions=frozenset()), prepared)
    assert journal.register(s.principal, prepared) == first
