"""Concrete per-effect source processing over scripted public owner reads."""

from types import SimpleNamespace

import pytest
from amphora_agent_planning.owner_handoff.history import HandoffHistory
from amphora_agent_planning.owner_handoff.preparation import HandoffPreparer
from amphora_agent_planning.owner_handoff.prepared import PreparedHandoff
from amphora_agent_planning.owner_handoff.selection import HandoffSelection

from ..research_proposals.support import ResearchCase
from ..result_publication.test_preparation import preparation


def case(kind="question"):
    test = preparation(None if kind == "graph" else ResearchCase())
    principal = test.bound.publication.identity.actor_id
    from amphora_agent_planning.access import Principal
    actor = Principal(principal, test.case.scope, frozenset({"record_attempts", "read_attempts"}))
    history = HandoffHistory(test.history.task, test.history.projection, test.history.observation, None, test.history.interpretation)
    selection = HandoffSelection.bind(actor, history.projection.reference(), "publication", kind,
        "graph" if kind == "graph" else "q", "owner")
    preparer = HandoffPreparer(test.case.data, knowledge=test.preparer.knowledge)
    return SimpleNamespace(test=test, actor=actor, history=history, selection=selection, preparer=preparer)


@pytest.mark.parametrize("kind", ["question", "graph"])
def test_preparation_and_each_new_write_recheck_source_and_interpretation(kind):
    bound = case(kind)
    inputs = bound.preparer.prepare(bound.history, bound.selection)
    payload = PreparedHandoff.create(bound.actor, bound.selection, bound.history, inputs.sources,
        questions=inputs.questions, knowledge=inputs.knowledge)
    before = len(bound.test.case.data.calls)
    bound.preparer.authorize(bound.history, payload, seconds=20)
    calls = bound.test.case.data.calls[before:]
    assert ("processing-content", "source-utf8") in calls
    assert ("processing-content", "output") in calls


@pytest.mark.parametrize("artifact", ["source-utf8", "output"])
def test_prepared_request_is_not_a_lasting_permission(artifact):
    bound = case()
    inputs = bound.preparer.prepare(bound.history, bound.selection)
    payload = PreparedHandoff.create(bound.actor, bound.selection, bound.history, inputs.sources, questions=inputs.questions)
    original = bound.test.case.data.content
    def content(reference, budget):
        if reference.artifact_id == artifact:
            raise ValueError("source_access_denied")
        return original(reference, budget)
    bound.test.case.data.content = content
    with pytest.raises(ValueError, match="source_access_denied"):
        bound.preparer.authorize(bound.history, payload, seconds=20)


def test_question_preparation_does_not_depend_on_knowledge_peer():
    bound = case()
    class Forbidden:
        def review(self, *_args, **_kwargs):
            raise AssertionError("unrelated owner lane")
    bound.preparer.knowledge = Forbidden()
    assert bound.preparer.prepare(bound.history, bound.selection).knowledge is None


def test_configured_question_reader_is_used_for_research_context():
    from amphora_agent_planning.research_proposals import QuestionContext
    bound = case()
    calls = []
    class Reader:
        def review(self, task, window):
            window.remaining()
            calls.append(task.sha256)
            return QuestionContext.bind(task, ())
    bound.preparer.research = Reader()
    result = bound.preparer.prepare(bound.history, bound.selection)
    assert calls == [bound.history.task.sha256] and result.questions.task_sha256 == calls[0]
