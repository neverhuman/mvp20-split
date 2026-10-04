from dataclasses import replace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.extraction import TraceProjection
from amphora_agent_planning.owner_handoff.history import HandoffHistory
from amphora_agent_planning.owner_handoff.prepared import PreparedHandoff
from amphora_agent_planning.owner_handoff.selection import HandoffSelection

from ..proposals.support import Case
from ..research_proposals.support import ResearchCase


def prepared(kind="question", *, existing=False):
    case = Case(history=existing) if kind == "graph" else ResearchCase()
    if existing and kind == "need":
        question = case.known_question()
        case.draft["evidence_needs"][0].update(question_local_id=None, question=question.reference.model_dump(mode="json"))
    bound = case.bind()
    projection = TraceProjection(bound.publication.payload.artifact.body)
    history = HandoffHistory(bound.task, projection, bound.observation, None, bound.publication)
    principal = Principal("fixture", case.scope, frozenset({"read_attempts", "record_attempts"}))
    selection = HandoffSelection.bind(principal, projection.reference(), "publication", kind,
        {"question": "q", "need": "n", "graph": "graph"}[kind], "owner")
    questions = None if kind == "graph" else case.bindings()[1]
    payload = PreparedHandoff.create(principal, selection, history, bound.review,
        questions=questions, knowledge=bound.knowledge)
    return payload, principal, selection, history


def row(payload):
    return {"body_bytes": payload.request.canonical, "review_bytes": payload.review.canonical,
        "witness_bytes": payload.witness, "manifest_bytes": payload.manifest, "payload_sha256": payload.sha256}


@pytest.mark.parametrize("kind,existing", [("question", False), ("need", False), ("need", True), ("graph", False), ("graph", True)])
def test_first_request_replays_without_source_bytes_or_scientific_revalidation(kind, existing):
    payload, principal, selection, history = prepared(kind, existing=existing)
    assert PreparedHandoff.restore(row(payload), replace(principal, actions=frozenset({"read_attempts"})), selection, history) == payload
    dependency = payload.dependency(history)
    if kind == "need" and not existing:
        question_selection, question = dependency
        assert question_selection.document()["local_id"] == "q"
        assert payload.request.document().question == question.reference
    else:
        assert dependency is None


@pytest.mark.parametrize("field", ["body_bytes", "review_bytes", "witness_bytes", "manifest_bytes", "payload_sha256"])
def test_historical_preparation_detects_changed_bytes(field):
    payload, principal, selection, history = prepared()
    stored = row(payload)
    stored[field] = "0" * 64 if field == "payload_sha256" else stored[field] + b" "
    with pytest.raises(ValueError):
        PreparedHandoff.restore(stored, principal, selection, history)
