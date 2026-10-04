import json
from dataclasses import replace

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.publication.journal import PublicationJournal
from amphora_agent_planning.publication.records import encode
from amphora_agent_planning.publication.store import PublicationStore
from amphora_agent_planning.research_proposals import QuestionContext
from amphora_agent_planning.result_publication.history import ResultHistory
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.prepared import (
    PreparedResult,
    restore_questions,
)
from amphora_agent_planning.result_publication.selection import ResultSelection
from amphora_agent_planning.result_publication.store import ResultStore

from ..publication.test_values import receipts
from ..research_proposals.support import ResearchCase
from .test_journal import setup_result


def answer_history(stored):
    case = ResearchCase(scope=stored.principal.scope)
    bound = case.bind()
    task = bound.task
    stored.journal.register(stored.principal, task.request)
    extractions = ExtractionJournal(stored.engine)
    extractions.register(stored.principal, task)
    binding = AttemptBinding(task.request, 1)
    stored.journal.begin_attempt(stored.principal, binding)
    stored.journal.record(stored.principal, binding, bound.observation)
    projection = extractions.record(stored.principal, task.document().task_id, binding.reference(), "candidate-trace").projection
    owner = PublicationStore(stored.engine, "data-owner")
    identity = owner.register(stored.principal, "publication", projection.reference())
    traces = PublicationJournal(owner)
    lease = owner.acquire(stored.principal, "publication")
    state = traces.prepare(stored.principal, lease, bound.review)
    upload, stream, receipt, derivation = receipts(identity, state.payload.artifact, state.attempt)
    for action, value in [("begun", upload.model_dump(mode="json")), ("streaming", None),
        ("streamed", stream.model_dump(mode="json")), ("finalizing", None),
        ("finalized", {"receipt": receipt.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json")})]:
        state = traces.advance(stored.principal, lease, state.position, action, value)
    owner.release(stored.principal, lease)
    selected = ResultSelection.bind(stored.principal, projection.reference(), "publication", "answer", "a", "data-owner")
    return traces, selected, bound.review, QuestionContext.bind(task, ())


@pytest.mark.postgres
def test_answer_preparation_replays_with_question_witness_but_without_source_processing(stored):
    _traces, selected, review, questions = answer_history(stored)
    store = ResultStore(stored.engine, "data-owner", trace_publisher_id="data-owner")
    journal = ResultJournal(store)
    store.register(stored.principal, selected)
    lease = store.acquire(stored.principal, selected.publication_id)
    state = journal.prepare(stored.principal, lease, review, questions=questions)
    assert json.loads(state.payload.artifact.body)["authority"] == "proposal_only"
    assert json.loads(state.payload.questions) == {"records": [], "gaps": []}
    assert journal.read(replace(stored.principal, actions=frozenset({"read_attempts"})), selected.publication_id) == state
    with pytest.raises(ValueError, match="result_answer_context"):
        journal.prepare(stored.principal, lease, review)


def row(payload):
    return {"body_bytes": payload.artifact.body, "review_bytes": payload.review.canonical,
        "question_bytes": payload.questions, "manifest_bytes": payload.manifest, "payload_sha256": payload.sha256}


@pytest.mark.postgres
@pytest.mark.parametrize("fault", ["digest", "manifest", "body", "ancestry", "review", "question_json"])
def test_stored_preparation_cannot_change_payload_or_provenance(stored, fault):
    store, journal, selected, review, feedback = setup_result(stored)
    lease = store.acquire(stored.principal, selected.publication_id)
    state = journal.prepare(stored.principal, lease, review, feedback=feedback)
    with stored.engine.begin() as connection:
        history = ResultHistory.load(connection, stored.principal, selected, store.traces)
    corrupted = row(state.payload)
    if fault == "digest": corrupted["payload_sha256"] = "0" * 64
    if fault == "manifest":
        corrupted["manifest_bytes"] = encode(json.loads(corrupted["manifest_bytes"]) | {"task_sha256": "0" * 64})
    if fault == "body": corrupted["body_bytes"] += b" "
    if fault == "ancestry":
        value = json.loads(corrupted["manifest_bytes"])
        value["declaration"]["inputs"].pop()
        corrupted["manifest_bytes"] = encode(value)
    if fault == "review":
        corrupted["review_bytes"] = encode(json.loads(corrupted["review_bytes"]) | {"task_sha256": "0" * 64})
    if fault == "question_json": corrupted["question_bytes"] = b'{"records":[],"records":[],"gaps":[]}'
    with pytest.raises(ValueError):
        PreparedResult.restore(corrupted, stored.principal, selected, history)


@pytest.mark.postgres
def test_question_witness_preserves_selected_records_and_explicit_gaps(stored):
    from amphora_agent_planning.result_publication.prepared import question_bytes
    case = ResearchCase(scope=stored.principal.scope)
    known = case.known_question()
    candidate, questions = case.bindings()
    assert restore_questions(question_bytes(candidate.task, questions), candidate.task) == questions
    gap = QuestionContext.bind(candidate.task, (), ((known.reference, "research_reference_unavailable"),))
    assert restore_questions(question_bytes(candidate.task, gap), candidate.task) == gap
    with pytest.raises(ValueError, match="result_question_task_binding"):
        question_bytes(candidate.task, replace(questions, task_sha256="0" * 64))


@pytest.mark.postgres
def test_missing_diagnostics_never_prepares(stored):
    store, journal, selected, review, _feedback = setup_result(stored)
    lease = store.acquire(stored.principal, selected.publication_id)
    with pytest.raises(ValueError, match="result_diagnostics_missing"):
        journal.prepare(stored.principal, lease, review)
    assert journal.read(stored.principal, selected.publication_id).payload is None
