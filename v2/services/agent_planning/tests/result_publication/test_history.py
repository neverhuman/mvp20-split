from dataclasses import replace

import pytest
from amphora_agent_planning.result_publication.history import ResultHistory
from amphora_agent_planning.result_publication.identity import ResultIdentity
from amphora_agent_planning.result_publication.selection import ResultSelection

from ..publication.test_journal import setup
from ..publication.test_values import receipts
from .test_payloads import prepared


def test_selection_and_payload_identity_share_slot_without_forging_write_authority():
    _, projection, _, artifact, _, principal = prepared()
    selected = ResultSelection.bind(principal, projection.reference(), "interpretation", "feedback", "diagnostics", "data-owner")
    identity = ResultIdentity.bind(principal, projection.reference(), "feedback", "diagnostics", "data-owner", artifact)
    assert selected.publication_id == identity.publication_id
    reader = replace(principal, actions=frozenset({"read_attempts"}))
    assert ResultSelection.restore(selected.canonical, reader) == selected
    alternate = ResultSelection.bind(principal, projection.reference(), "another", "feedback", "diagnostics", "new-config")
    assert alternate.publication_id == selected.publication_id and alternate.sha256 != selected.sha256
    with pytest.raises(PermissionError):
        ResultSelection.bind(reader, projection.reference(), "interpretation", "feedback", "diagnostics", "data-owner")
    with pytest.raises(ValueError, match="result_selection_canonical"):
        ResultSelection.restore(selected.canonical + b" ", reader)


def finalize(stored):
    store, journal, identity, review, artifact = setup(stored)
    lease = store.acquire(stored.principal, "publication")
    state = journal.prepare(stored.principal, lease, review)
    upload, stream, receipt, derivation = receipts(identity, artifact, state.attempt)
    for action, value in [("begun", upload.model_dump(mode="json")), ("streaming", None),
        ("streamed", stream.model_dump(mode="json")), ("finalizing", None),
        ("finalized", {"receipt": receipt.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json")})]:
        state = journal.advance(stored.principal, lease, state.position, action, value)
    store.release(stored.principal, lease)
    selection = ResultSelection.bind(stored.principal, identity.trace(), "publication", "feedback", "diagnostics", "data-owner")
    return journal, selection, review


@pytest.mark.postgres
def test_history_loads_owned_facts_and_exact_finalized_interpretation(stored):
    journal, selection, review = finalize(stored)
    with stored.engine.begin() as connection:
        facts = ResultHistory.load(connection, stored.principal, selection, journal)
    assert facts.task == review.task and facts.projection.reference() == selection.trace()
    assert facts.interpretation.attempt.stage == "finalized" and facts.prior is None
    assert facts.arguments(review) == (facts.task, facts.observation, review, facts.interpretation)
    reader = replace(stored.principal, actions=frozenset({"read_attempts"}))
    with stored.engine.begin() as connection:
        assert ResultHistory.load(connection, reader, selection, journal) == facts


@pytest.mark.postgres
@pytest.mark.parametrize("fault", ["unknown_trace", "unknown_interpretation", "wrong_actor"])
def test_owned_origin_cannot_be_replaced_by_hash_shaped_reference(stored, fault):
    journal, selection, _ = finalize(stored)
    principal = stored.principal
    if fault == "unknown_trace":
        selection = ResultSelection.bind(principal, selection.trace().model_copy(update={"trace_id": "unknown"}),
            "publication", "feedback", "diagnostics", "data-owner")
    if fault == "unknown_interpretation":
        selection = ResultSelection.bind(principal, selection.trace(), "unknown", "feedback", "diagnostics", "data-owner")
    if fault == "wrong_actor":
        principal = replace(principal, actor_id="other")
        selection = ResultSelection.bind(principal, selection.trace(), "publication", "feedback", "diagnostics", "data-owner")
    with stored.engine.begin() as connection, pytest.raises(ValueError):
        ResultHistory.load(connection, principal, selection, journal)


@pytest.mark.postgres
def test_unfinalized_interpretation_is_not_a_result_origin(stored):
    _, journal, identity, _, _ = setup(stored)
    selection = ResultSelection.bind(stored.principal, identity.trace(), "publication", "feedback", "diagnostics", "data-owner")
    with stored.engine.begin() as connection, pytest.raises(ValueError, match="interpretation_not_published"):
        ResultHistory.load(connection, stored.principal, selection, journal)


@pytest.mark.postgres
def test_repaired_trace_retains_exact_prior_owned_history(stored):
    from amphora_agent_planning.context import AttemptBinding
    from amphora_agent_planning.persistence.extraction import ExtractionJournal
    from amphora_agent_planning.providers import observe

    from ..extraction.test_trace import Response

    traces, parent, review = finalize(stored)
    with stored.engine.begin() as connection:
        original = ResultHistory.load(connection, stored.principal, parent, traces)
    binding = AttemptBinding(original.task.request, 2)
    stored.journal.begin_attempt(stored.principal, binding)
    observed = observe(binding, Response(original.observation.capture.content))
    stored.journal.record(stored.principal, binding, observed)
    child = ExtractionJournal(stored.engine).record(stored.principal, original.task.document().task_id,
        binding.reference(), "child", parent.trace()).projection
    identity = traces.store.register(stored.principal, "child-interpretation", child.reference())
    lease = traces.store.acquire(stored.principal, "child-interpretation")
    state = traces.prepare(stored.principal, lease, review)
    upload, stream, receipt, derivation = receipts(identity, state.payload.artifact, state.attempt)
    for action, value in [("begun", upload.model_dump(mode="json")), ("streaming", None),
        ("streamed", stream.model_dump(mode="json")), ("finalizing", None),
        ("finalized", {"receipt": receipt.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json")})]:
        state = traces.advance(stored.principal, lease, state.position, action, value)
    traces.store.release(stored.principal, lease)
    selected = ResultSelection.bind(stored.principal, child.reference(), "child-interpretation", "feedback", "diagnostics", "data-owner")
    with stored.engine.begin() as connection:
        history = ResultHistory.load(connection, stored.principal, selected, traces)
    assert history.prior == original.projection and history.projection.document().repair_depth == 1
