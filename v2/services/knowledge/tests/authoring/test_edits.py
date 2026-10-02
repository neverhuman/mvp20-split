"""Semantic edit oracles; synthetic references are not remote validation receipts."""

import json
from dataclasses import replace

import pytest
from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AddAssertion,
    CorrectAssertion,
    DomainHead,
    EntityAlias,
    GraphChangeProposal,
    MergeEntities,
    RetractAssertion,
    ReviseEntityContext,
)
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.authoring.entities import EntityHistory
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.authoring.references import ReferencedInputs


def head(state, change_id="prior"):
    # This is an explicit test-only head. Real log fingerprints require the replay/ledger owner.
    return DomainHead(snapshot=state.reference, change=AcceptedChangeRef(graph=state.graph,
        change_id=change_id, position=state.revision, sha256="f"*64))


def next_edit(fixture, state, operations, change_id="next"):
    current = head(state)
    proposal = fixture.proposal.model_copy(update={"base": current, "change_id": change_id, "operations": tuple(operations)})
    return state.apply(proposal, current)


def test_canonical_snapshot_preserves_meaning_and_independent_entity_order(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    reordered = e.proposal.model_copy(update={"operations": (e.proposal.operations[1], e.proposal.operations[0], e.proposal.operations[2])})
    second = e.state.apply(reordered, None)
    assert first.to_snapshot() == second.to_snapshot()
    claim = first.assertions.active()[0]
    assert claim.statement == "A correlates with B under synthetic conditions."
    assert claim.posture == "hypothesis" and claim.predicate == "correlates_with"
    assert claim.research_links[0].question.question_id == "question"
    assert e.state.entities.records == () and e.state.revision == 0


def test_failed_later_operation_never_leaves_a_partial_edit(graph_fixture):
    e = graph_fixture
    bad = e.proposal.model_copy(update={"operations": (*e.proposal.operations, e.proposal.operations[0])})
    with pytest.raises(KnowledgeError, match="entity_identity_reuse"):
        e.state.apply(bad, None)
    assert e.state.entities.records == ()
    with pytest.raises(KnowledgeError, match="unpublished_graph"):
        e.state.to_snapshot()


def test_correction_retains_original_interpretation_and_overriding_provenance(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    prior = first.assertions.active()[0]
    grounding = prior.grounding.model_copy(update={"conversion_traces": (
        prior.grounding.conversion_traces[0].model_copy(update={"trace_id": "override-trace"}),)})
    corrected = prior.model_copy(update={"reference": prior.reference.model_copy(update={"revision": 2}),
        "supersedes": prior.reference, "polarity": "negated", "grounding": grounding})
    after = next_edit(e, first, [CorrectAssertion(operation="correct_assertion", prior=prior.reference, replacement=corrected)])
    assert after.assertions.records == (prior, corrected)
    assert after.assertions.active() == (corrected,)
    assert prior.grounding.conversion_traces[0].trace_id == "conversion"
    assert corrected.grounding.conversion_traces[0].trace_id == "override-trace"
    assert first.assertions.active() == (prior,)


def test_incompatible_answers_remain_distinct_contextual_evidence(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    original = first.assertions.active()[0]
    other = original.model_copy(update={"reference": original.reference.model_copy(update={"assertion_id": "opposite"}),
        "polarity": "negated", "posture": "unresolved", "applicability": original.applicability.model_copy(update={"artifact_id": "other-context"})})
    after = next_edit(e, first, [AddAssertion(operation="add_assertion", assertion=other)])
    assert after.assertions.active() == (original, other)
    assert len({claim.applicability.artifact_id for claim in after.assertions.active()}) == 2


def test_retraction_never_reuses_or_resurrects_identity(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    original = first.assertions.active()[0]
    after = next_edit(e, first, [RetractAssertion(operation="retract_assertion", assertion=original.reference)])
    assert after.assertions.records == (original,) and after.assertions.active() == ()
    assert after.assertions.retractions[0].change_id == "next"
    with pytest.raises(KnowledgeError, match="assertion_identity_reuse"):
        next_edit(e, after, [AddAssertion(operation="add_assertion", assertion=original)])
    replacement = original.model_copy(update={"reference": original.reference.model_copy(update={"revision": 2}), "supersedes": original.reference})
    with pytest.raises(KnowledgeError, match="assertion_retracted"):
        next_edit(e, after, [CorrectAssertion(operation="correct_assertion", prior=original.reference, replacement=replacement)])


def test_merge_keeps_original_assertion_endpoints_and_both_entities(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    left, right = first.entities.records
    after = next_edit(e, first, [MergeEntities(operation="merge_entities", source=left.reference, target=right.reference)])
    assert after.entities.records == first.entities.records
    assert after.assertions.records == first.assertions.records
    assert after.entities.resolve(left.reference) == right.reference
    assert after.assertions.active()[0].subject == left.reference
    with pytest.raises(KnowledgeError, match="entity_already_merged"):
        next_edit(e, after, [MergeEntities(operation="merge_entities", source=right.reference, target=left.reference)])
    corrupt = EntityHistory(first.entities.records, (
        EntityAlias(source=left.reference, target=right.reference, change_id="one"),
        EntityAlias(source=right.reference, target=left.reference, change_id="two")))
    with pytest.raises(KnowledgeError, match="alias_cycle"):
        corrupt.resolve(left.reference)


def test_context_revision_does_not_rewrite_old_entity_or_allow_identity_edits(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    old = first.entities.records[0]
    new = old.model_copy(update={"reference": old.reference.model_copy(update={"revision": 2}),
        "supersedes": old.reference, "context": old.context.model_copy(update={"artifact_id": "new-context"})})
    operation = ReviseEntityContext(operation="revise_entity_context", prior=old.reference, replacement=new)
    after = next_edit(e, first, [operation])
    assert after.entities.find(old.reference) == old and after.entities.find(new.reference) == new
    with pytest.raises(KnowledgeError, match="context_edit_changes_identity"):
        next_edit(e, first, [operation.model_copy(update={"replacement": new.model_copy(update={"label": "unrelated"})})])
    with pytest.raises(KnowledgeError, match="stale_entity_revision"):
        next_edit(e, after, [operation])


@pytest.mark.parametrize("mutation,code", [
    (lambda c: c["operations"][0]["entity"]["reference"]["graph"].update(graph_id="foreign"), "reference_graph_mismatch"),
    (lambda c: c["operations"][0]["entity"]["context"]["scope"].update(project_id="foreign"), "reference_scope_mismatch"),
    (lambda c: c["operations"][2]["assertion"]["research_links"][0]["question"]["scope"].update(project_id="foreign"), "reference_scope_mismatch"),
    (lambda c: c["grounding"]["spans"][0].update(end=1000), "source_span_bounds"),
    (lambda c: c["operations"][0]["entity"]["context"].update(sha256="0"*64), "reference_identity_conflict"),
    (lambda c: c["operations"][2]["assertion"].update(predicate="invented"), "unknown_predicate"),
    (lambda c: c["operations"][2]["assertion"]["subject"].update(entity_id="missing"), "unknown_entity_revision"),
], ids=["foreign-graph", "foreign-artifact", "foreign-question", "span-overflow", "artifact-equivocation", "predicate", "endpoint"])
def test_cross_record_semantics_reject_shape_valid_requests(graph_fixture, mutation, code):
    e = graph_fixture
    raw = e.proposal.model_dump(mode="json")
    mutation(raw)
    proposal = GraphChangeProposal.model_validate_json(json.dumps(raw))
    with pytest.raises(KnowledgeError, match=code):
        e.state.apply(proposal, None)


def test_stale_head_or_substituted_configuration_is_not_rebased(graph_fixture):
    e = graph_fixture
    first = e.state.apply(e.proposal, None)
    with pytest.raises(KnowledgeError, match="stale_head"):
        first.apply(e.proposal, head(first))
    with pytest.raises(KnowledgeError, match="invalid_current_head"):
        first.apply(e.proposal, None)
    substituted = e.proposal.model_copy(update={"policy": e.proposal.policy.model_copy(update={"sha256": "0"*64})})
    with pytest.raises(KnowledgeError, match="graph_configuration_mismatch"):
        e.state.apply(substituted, None)


def test_policy_counts_history_and_reference_collection_deduplicates_exact_refs(graph_fixture):
    e = graph_fixture
    inputs = ReferencedInputs.collect(e.proposal)
    assert tuple(map(len, (inputs.artifacts, inputs.sources, inputs.traces, inputs.questions, inputs.needs, inputs.spans))) == (1, 1, 1, 1, 1, 1)
    policy = StructuralPolicy(max_entities=1)
    bounded = replace(e.state, policy=policy)
    proposal = e.proposal.model_copy(update={"policy": policy.reference})
    with pytest.raises(KnowledgeError, match="graph_history_limit"):
        bounded.apply(proposal, None)
    assert bounded.entities.records == ()
