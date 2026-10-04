"""Owned multi-effect ordering with scripted peers and real result publication."""

from types import SimpleNamespace

import pytest
from amphora_agent_planning.owner_handoff.coordinator import HandoffCoordinator
from amphora_agent_planning.owner_handoff.journal import HandoffJournal
from amphora_agent_planning.owner_handoff.store import HandoffStore
from amphora_agent_planning.owner_handoff.transport import OwnerAbsent, OwnerDenied
from amphora_agent_planning.owner_handoff.workflow import OwnerHandoff
from amphora_agent_planning.result_publication.history import ResultHistory
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.prepared import PreparedResult
from amphora_agent_planning.result_publication.store import ResultStore
from amphora_agent_planning.result_publication.workflow import (
    ResultInputs,
    ResultPublisher,
)
from amphora_tool_protocol import ArtifactClient, WorkerIdentity

from ..publication.test_workflow import DataPeer
from ..result_publication import test_prepared as origins
from .test_workflow import Preparer

pytestmark = pytest.mark.postgres


class ResearchPeer:
    owner_id, owner = "research", "research"

    def __init__(self):
        self.records, self.calls, self.denied = {}, [], set()

    def read(self, request, window, guard):
        window.start()
        guard()
        slot = request.selection.document()["local_id"]
        self.calls.append(("read", request.kind, slot))
        if slot in self.denied:
            raise OwnerDenied("denied")
        if request.selection.effect_id not in self.records:
            raise OwnerAbsent("absent")
        return self.records[request.selection.effect_id]

    def submit(self, request, window, guard):
        window.start()
        guard()
        self.calls.append(("write", request.kind, request.selection.document()["local_id"]))
        record = request.document()
        if request.kind == "need":
            assert any(getattr(existing, "reference", None) == record.question for existing in self.records.values())
        self.records[request.selection.effect_id] = record
        return record


def coordinator(stored, external=None):
    traces, answer, review, questions = origins.answer_history(stored)
    if external is not None:
        from amphora_agent_planning.research_proposals import QuestionContext
        questions = QuestionContext.bind(review.task, (external,))
    store = HandoffStore(stored.engine, "research", trace_publisher_id="data-owner")
    peer = ResearchPeer()
    researcher = OwnerHandoff(HandoffJournal(store), Preparer(stored.engine, review, questions), peer)
    results = ResultJournal(ResultStore(stored.engine, "data-owner", trace_publisher_id="data-owner"))
    with stored.engine.begin() as connection:
        history = ResultHistory.load(connection, stored.principal, answer, traces)
    prepared = PreparedResult.create(stored.principal, answer, history, review, questions=questions)
    data = DataPeer(prepared.identity, prepared.artifact)
    class AnswerPreparer:
        def prepare(self, _history, _selection):
            assert external is not None or any(kind == "question" for method, kind, _ in peer.calls if method == "write")
            return ResultInputs(review, questions=questions)
    publisher = ResultPublisher(results, AnswerPreparer(), ArtifactClient(data, WorkerIdentity(stored.principal.actor_id, stored.principal.scope)))
    return HandoffCoordinator(traces, research=researcher, answers=publisher), answer.trace(), peer, data


def test_questions_precede_needs_and_answer_artifacts_and_replay_has_no_effects(stored):
    owner, trace, research, data = coordinator(stored)
    result = owner.run(stored.principal, trace, "publication")
    assert [(item.slot.kind, item.status) for item in result.effects] == [
        ("question", "acknowledged"), ("need", "acknowledged"), ("answer", "finalized")]
    assert [kind for method, kind, _ in research.calls if method == "write"] == ["question", "need"]
    assert data.calls
    calls = (list(research.calls), list(data.calls))
    assert owner.run(stored.principal, trace, "publication") == result
    assert (research.calls, data.calls) == calls


def test_unacknowledged_question_blocks_only_dependent_writes(stored):
    owner, trace, research, data = coordinator(stored)
    research.denied.add("q")
    result = owner.run(stored.principal, trace, "publication")
    assert [item.reason for item in result.effects] == ["owner_access_denied", "dependency_unavailable", "dependency_unavailable"]
    assert not data.calls and not any(method == "write" for method, _, _ in research.calls)


def test_owner_failure_does_not_prevent_an_independent_graph_slot(stored, monkeypatch):
    from ..proposals.support import Case
    from ..research_proposals.support import ResearchCase

    case = ResearchCase(scope=stored.principal.scope)
    graph = Case(scope=stored.principal.scope)
    case.draft.update(entities=graph.draft["entities"], assertions=graph.draft["assertions"])
    monkeypatch.setattr(origins, "ResearchCase", lambda scope: case)
    owner, trace, research, data = coordinator(stored)
    research.denied.add("q")
    visited = []
    def submit(principal, selection):
        visited.append(selection.document()["kind"])
        raise ValueError("handoff_lease_unavailable")
    owner.knowledge = SimpleNamespace(journal=SimpleNamespace(store=SimpleNamespace(owner_id="knowledge")), submit=submit)
    result = owner.run(stored.principal, trace, "publication")
    assert visited == ["graph"] and result.effects[-1].reason == "busy"
    assert not data.calls


def test_unconfigured_lanes_remain_explicit(stored):
    owner, trace, _, _ = coordinator(stored)
    owner.research = owner.answers = None
    result = owner.run(stored.principal, trace, "publication")
    assert len(result.effects) == 3 and all(item.reason == "owner_unconfigured" for item in result.effects)


@pytest.mark.parametrize("availability", ["exact", "missing", "unconfigured"])
def test_external_answer_requires_exact_selected_question(stored, monkeypatch, availability):
    from amphora_agent_planning.research_proposals import QuestionContext

    from ..research_proposals.support import ResearchCase

    case = ResearchCase(scope=stored.principal.scope)
    question = case.known_question()
    case.draft["questions"] = []
    case.draft["evidence_needs"] = []
    case.draft["answers"][0].update(question_local_id=None, question=question.reference.model_dump(mode="json"))
    monkeypatch.setattr(origins, "ResearchCase", lambda scope: case)
    owner, trace, peer, data = coordinator(stored, external=question)
    class Reader:
        def review(self, task):
            if availability == "exact":
                return QuestionContext.bind(task, (question,))
            return QuestionContext.bind(task, (), ((question.reference, "research_reference_unavailable"),))
    owner.questions = None if availability == "unconfigured" else Reader()
    report = owner.run(stored.principal, trace, "publication")
    assert len(report.effects) == 1 and not peer.calls
    if availability == "exact":
        assert report.effects[0].status == "finalized" and data.calls
    else:
        assert report.effects[0].reason == "dependency_unavailable" and not data.calls


@pytest.mark.parametrize("fault,reason", [(PermissionError("private scope"), "access_denied"),
    (ValueError("handoff_configuration_conflict"), "identity_conflict"),
    (ValueError("untrusted peer details"), "effect_unavailable")])
def test_one_owner_failure_is_safely_reported_per_effect(stored, fault, reason):
    owner, trace, _, data = coordinator(stored)
    def fail(*args):
        raise fault
    owner.research.submit = fail
    report = owner.run(stored.principal, trace, "publication")
    assert [item.reason for item in report.effects] == [reason, reason, "dependency_unavailable"]
    assert not data.calls


def test_missing_research_owner_does_not_publish_dependent_answer(stored):
    owner, trace, _, data = coordinator(stored)
    owner.research = None
    report = owner.run(stored.principal, trace, "publication")
    assert report.effects[-1].reason == "dependency_unavailable" and not data.calls
