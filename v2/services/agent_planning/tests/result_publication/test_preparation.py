"""Actual preparation and diagnostic policy over scripted public owner records."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.extraction import TraceProjection
from amphora_agent_planning.result_publication.diagnostics import NoRepairNeeded
from amphora_agent_planning.result_publication.history import ResultHistory
from amphora_agent_planning.result_publication.payload import ResultArtifact
from amphora_agent_planning.result_publication.preparation import ResultPreparer
from amphora_agent_planning.result_publication.selection import ResultSelection
from amphora_agent_planning.source_access.budget import ReadBudget

from ..proposals.support import Case
from ..research_proposals.support import ResearchCase


def preparation(case=None, *, kind="feedback", knowledge=True):
    case = Case() if case is None else case
    bound = case.bind()
    projection = TraceProjection(bound.publication.payload.artifact.body)
    history = ResultHistory(bound.task, projection, bound.observation, None, bound.publication)
    reference = bound.publication.attempt.result.artifact
    case.data.artifacts[reference.artifact_id] = reference
    case.data.payloads[reference.artifact_id] = projection.canonical
    principal = Principal("fixture", case.scope, frozenset({"record_attempts", "read_attempts"}))
    selected = ResultSelection.bind(principal, projection.reference(), "publication", kind,
        "diagnostics" if kind == "feedback" else "a", "data-owner")
    class Knowledge:
        def review(self, task, window):
            assert task == history.task
            window.remaining()
            return bound.knowledge
    preparer = ResultPreparer(case.data, knowledge=Knowledge() if knowledge else None)
    case.data.calls.clear()
    return SimpleNamespace(case=case, bound=bound, history=history, selection=selected, preparer=preparer)


def test_structural_feedback_preserves_useful_items_and_actual_capture():
    case = ResearchCase()
    case.draft["answers"][0]["context"] = None
    test = preparation(case)
    result = test.preparer.prepare(test.history, test.selection)
    feedback = result.feedback.document()
    assert feedback.withheld_paths == ("/answers/0",)
    assert any(item.code == "required_context_missing" for item in feedback.findings)
    assert feedback.preserve_valid_items and feedback.authority == "diagnostic_only"
    assert feedback.parent == test.history.projection.reference()
    result.feedback.verify_history(test.history.task, test.history.projection, test.history.observation)
    assert ("processing-content", "output") in case.data.calls
    artifact = ResultArtifact.feedback(*test.history.arguments(result.sources), result.feedback)
    assert artifact.body == result.feedback.canonical


def test_graph_diagnostics_are_derived_from_reviewed_owner_context():
    case = Case()
    case.draft["entities"][0]["entity_type"] = "unknown-type"
    test = preparation(case)
    result = test.preparer.prepare(test.history, test.selection)
    assert "/entities/0" in result.feedback.document().withheld_paths
    assert any(item.code == "unknown_entity_type" for item in result.feedback.document().findings)


def test_useful_uncertain_science_does_not_request_another_model_call():
    test = preparation(ResearchCase())
    class Forbidden:
        def review(self, *_args, **_kwargs):
            raise AssertionError("Research-only diagnostics attempted graph reads")
    test.preparer.knowledge = Forbidden()
    with pytest.raises(NoRepairNeeded, match="no_structural_repair"):
        test.preparer.prepare(test.history, test.selection)


def test_missing_graph_reader_does_not_invent_invalid_graph_or_lose_research_diagnostics():
    case = Case()
    case.draft["entities"][0]["entity_type"] = "unknown-type"
    test = preparation(case, knowledge=False)
    with pytest.raises(NoRepairNeeded):
        test.preparer.prepare(test.history, test.selection)


@pytest.mark.parametrize("artifact", ["source-utf8", "output"])
def test_current_processing_denial_prevents_new_result_preparation(artifact):
    test = preparation(ResearchCase(), kind="answer")
    original = test.case.data.content
    def content(reference, budget):
        if reference.artifact_id == artifact:
            raise ValueError("source_access_denied")
        return original(reference, budget)
    test.case.data.content = content
    with pytest.raises(ValueError, match="source_access_denied"):
        test.preparer.prepare(test.history, test.selection)


def test_answer_needs_no_graph_reader_and_keeps_exact_question_gaps():
    case = ResearchCase()
    question = case.known_question()
    test = preparation(case, kind="answer")
    class Forbidden:
        def review(self, *_args, **_kwargs):
            raise AssertionError("Answer preparation attempted graph reads")
    test.preparer.knowledge = Forbidden()
    inputs = test.preparer.prepare(test.history, test.selection)
    assert inputs.feedback is None
    assert inputs.questions.unavailable() == ((question.reference, "research_reader_unconfigured"),)
    answer = ResultArtifact.answer(*test.history.arguments(inputs.sources), inputs.questions, "a")
    assert b'proposal_only' in answer.body


def test_changed_interpretation_bytes_are_not_accepted_as_history():
    test = preparation(ResearchCase(), kind="answer")
    test.case.data.payloads["output"] = b"substituted"
    with pytest.raises(ValueError, match="source_artifact_bytes"):
        test.preparer.prepare(test.history, test.selection)


def test_one_deadline_spans_source_and_owner_reads():
    test = preparation(ResearchCase(), kind="answer")
    budget = ReadBudget()
    class Research:
        def review(self, task, window):
            assert window.remaining() <= 15
            budget.deadline = 0
            from amphora_agent_planning.research_proposals import QuestionContext
            return QuestionContext.bind(task, ())
    test.preparer.research = Research()
    with pytest.raises(ValueError, match="source_review_deadline"):
        test.preparer.prepare(test.history, test.selection, budget=budget)


def test_wrong_selection_is_rejected_before_processing():
    test = preparation(ResearchCase(), kind="answer")
    changed = replace(test.history, projection=replace(test.history.projection,
        canonical=test.history.projection.canonical.replace(b'candidate-trace', b'foreign-trace')))
    with pytest.raises(ValueError, match="result_preparation_selection"):
        test.preparer.prepare(changed, test.selection)
    assert not test.case.data.calls


def test_missing_selected_question_is_not_repaired_by_spending_more_model_calls():
    case = ResearchCase()
    question = case.known_question()
    case.draft["answers"][0].update(question_local_id=None, question=question.reference.model_dump(mode="json"))
    test = preparation(case)
    with pytest.raises(NoRepairNeeded):
        test.preparer.prepare(test.history, test.selection)


def test_peer_unavailability_preserves_independent_structural_diagnostics():
    case = ResearchCase()
    case.draft["entities"] = Case().draft["entities"]
    case.draft["answers"][0]["context"] = None
    test = preparation(case)
    class Unavailable:
        def review(self, *_args, **_kwargs):
            from amphora_agent_planning.knowledge_access.transport import (
                KnowledgeUnavailable,
            )
            raise KnowledgeUnavailable("knowledge_peer_unavailable")
    test.preparer.knowledge = Unavailable()
    result = test.preparer.prepare(test.history, test.selection)
    codes = {item.code for item in result.feedback.document().findings}
    assert {"required_context_missing", "knowledge_context_unavailable"} <= codes
    assert result.feedback.document().withheld_paths == ("/answers/0",)


@pytest.mark.parametrize("output", [b"{", b"\xff"])
def test_missing_structured_output_keeps_exact_bytes_in_diagnostics(output):
    from amphora_agent_planning.context import AttemptBinding
    from amphora_agent_planning.providers import observe
    from amphora_agent_planning.result_publication.diagnostics import DiagnosticPolicy

    from ..persistence.test_extraction import Response
    test = preparation()
    observed = observe(AttemptBinding(test.history.task.request, 1), Response(output))
    projection = TraceProjection.derive("failed-trace", test.history.task, observed)
    history = replace(test.history, projection=projection, observation=observed)
    result = DiagnosticPolicy().feedback(history, test.bound.review, None)
    result.verify_history(history.task, projection, observed)
    assert result.document().withheld_paths == ("/output",)
    assert result.document().findings[0].code == "interpretation_output_unavailable"


def test_diagnostic_policy_rejects_unbound_history():
    from amphora_agent_planning.result_publication.diagnostics import DiagnosticPolicy
    test = preparation()
    history = replace(test.history, projection=replace(test.history.projection,
        canonical=test.history.projection.canonical.replace(b'"repair_depth":0', b'"repair_depth":1')))
    with pytest.raises(ValueError, match="result_history_binding"):
        DiagnosticPolicy().feedback(history, test.bound.review, None)
