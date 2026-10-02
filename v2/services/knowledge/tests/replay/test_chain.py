"""Replay uses accepted operations and an independently specified state oracle."""

from datetime import UTC, datetime, timedelta

import pytest
from amphora_contracts_knowledge import CorrectAssertion, ReferenceValidation, RetractAssertion
from amphora_knowledge.authoring.canonical import KnowledgeError, digest
from amphora_knowledge.authoring.references import ReferencedInputs
from amphora_knowledge.replay.accepted import AcceptedEdit
from amphora_knowledge.replay.chain import GraphReplay

NOW = datetime(2026, 10, 1, 23, 0, tzinfo=UTC)


def observation(proposal):
    # Test fixture supplies a declared observation; no remote verification is claimed.
    refs = ReferencedInputs.collect(proposal)
    return ReferenceValidation(checked_at=NOW, artifacts=refs.artifacts, sources=refs.sources,
        conversion_traces=refs.traces, questions=refs.questions, evidence_needs=refs.needs)


def review(state, head, proposal):
    return AcceptedEdit.review(state, head, proposal, actor_id="fixture-reviewer",
                               observation=observation(proposal), accepted_at=NOW + timedelta(seconds=1))


@pytest.fixture
def history(graph_fixture):
    e = graph_fixture
    first = review(e.state, None, e.proposal)
    original = first.state.assertions.active()[0]
    corrected = original.model_copy(update={"reference": original.reference.model_copy(update={"revision": 2}),
        "supersedes": original.reference, "polarity": "negated", "statement": "The original relationship is disputed."})
    change = e.proposal.model_copy(update={"change_id": "correction", "base": first.head,
        "operations": (CorrectAssertion(operation="correct_assertion", prior=original.reference, replacement=corrected),)})
    second = review(first.state, first.head, change)
    retraction = e.proposal.model_copy(update={"change_id": "retraction", "base": second.head,
        "operations": (RetractAssertion(operation="retract_assertion", assertion=corrected.reference),)})
    third = review(second.state, second.head, retraction)
    return e, (first, second, third)


def test_replay_reconstructs_corrections_links_and_tombstones_exactly(history):
    e, edits = history
    replay = GraphReplay(e.state.graph, e.vocabulary, e.policy)
    actual = replay.rebuild([edit.record for edit in edits])
    assert actual.state.to_snapshot() == edits[-1].state.to_snapshot()
    assert actual.head == edits[-1].head
    content = actual.state.to_content()
    assert [(r.reference.assertion_id, r.reference.revision, r.polarity) for r in content.assertions] == [
        ("claim", 1, "affirmed"), ("claim", 2, "negated")]
    assert [r.label for r in content.entities] == ["A", "B"]
    assert content.retractions[0].assertion.revision == 2
    assert content.assertions[0].research_links == content.assertions[1].research_links
    assert actual.state.assertions.active() == ()
    assert replay.rebuild([]).head is None


@pytest.mark.parametrize("variant,code", [
    ("missing", "replay_position_gap"), ("reordered", "replay_position_gap"),
    ("duplicate", "duplicate_accepted_change"), ("changed", "accepted_change_digest_mismatch"),
    ("forged-head", "replayed_change_mismatch"), ("foreign", "replay_graph_mismatch"),
])
def test_history_damage_is_not_skipped_or_reinterpreted(history, variant, code):
    e, edits = history
    records = [edit.record for edit in edits]
    if variant == "missing":
        records.pop(1)
    elif variant == "reordered":
        records.reverse()
    elif variant == "duplicate":
        records.insert(1, records[0])
    elif variant == "changed":
        records[0] = records[0].model_copy(update={"content": records[0].content.model_copy(update={"actor_id": "other"})})
    elif variant == "foreign":
        records[0] = records[0].model_copy(update={"reference": records[0].reference.model_copy(update={
            "graph": records[0].reference.graph.model_copy(update={"graph_id": "foreign"})})})
    else:
        content = records[0].content.model_copy(update={"resulting_snapshot": records[0].content.resulting_snapshot.model_copy(update={"sha256": "0"*64})})
        records[0] = records[0].model_copy(update={"content": content,
            "reference": records[0].reference.model_copy(update={"sha256": digest(content)})})
    with pytest.raises(KnowledgeError, match=code):
        GraphReplay(e.state.graph, e.vocabulary, e.policy).rebuild(records)


def test_replay_is_bounded_and_does_not_trust_new_policy(history):
    e, edits = history
    with pytest.raises(KnowledgeError, match="replay_limit"):
        GraphReplay(e.state.graph, e.vocabulary, e.policy, max_changes=1).rebuild([r.record for r in edits])
    record = edits[0].record
    content = record.content.model_copy(update={"policy": record.content.policy.model_copy(update={"sha256": "0"*64})})
    forged = record.model_copy(update={"content": content, "reference": record.reference.model_copy(update={"sha256": digest(content)})})
    with pytest.raises(KnowledgeError, match="replay_policy_mismatch"):
        GraphReplay(e.state.graph, e.vocabulary, e.policy).rebuild([forged])


def test_review_needs_exact_reference_observation_and_nonfuture_time(graph_fixture):
    e = graph_fixture
    observed = observation(e.proposal)
    with pytest.raises(KnowledgeError, match="reference_validation_mismatch"):
        AcceptedEdit.review(e.state, None, e.proposal, actor_id="fixture", accepted_at=NOW,
                            observation=observed.model_copy(update={"questions": ()}))
    with pytest.raises(KnowledgeError, match="invalid_review_time"):
        AcceptedEdit.review(e.state, None, e.proposal, actor_id="fixture", accepted_at=NOW - timedelta(seconds=1),
                            observation=observed)


def test_review_timestamp_changes_log_identity_but_not_semantic_snapshot(graph_fixture):
    e = graph_fixture
    first = review(e.state, None, e.proposal)
    later = AcceptedEdit.review(e.state, None, e.proposal, actor_id="fixture-reviewer", observation=observation(e.proposal),
                                accepted_at=NOW + timedelta(seconds=2))
    assert first.state.reference == later.state.reference
    assert first.record.reference.sha256 != later.record.reference.sha256
