import pytest
from amphora_contracts_knowledge import AddAssertion
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.reasoning.binding import GraphInputs
from amphora_knowledge.reasoning.evaluator import Evaluator
from amphora_knowledge.reasoning.model import Program

from ..replay.test_chain import history as history
from ..replay.test_chain import review


def test_input_binding_pins_snapshot_context_and_original_assertion(history):
    _, edits = history
    state = edits[0].state
    assertion = state.assertions.active()[0]
    bound = GraphInputs.from_state(state, assertion.applicability)
    result = Evaluator().evaluate(Program("fixture-v1", ()), bound.seeds)
    fact = bound.fact(assertion.reference)
    assert bound.snapshot == edits[0].head.snapshot and bound.context == assertion.applicability
    assert bound.references(result.origins(fact)) == (assertion.reference,)
    assert result.assess(fact).status == "supported"
    # Logical support from a represented statement does not promote its posture.
    assert assertion.posture == "hypothesis"


def test_corrected_snapshot_excludes_stale_revision_and_retraction(history):
    _, edits = history
    original = edits[0].state.assertions.active()[0]
    corrected = GraphInputs.from_state(edits[1].state, original.applicability)
    assert corrected.snapshot != edits[0].head.snapshot
    assert len(corrected.seeds) == 1 and corrected.seeds[0].fact.polarity == "negated"
    with pytest.raises(KnowledgeError, match="reasoning_assertion_not_applicable"):
        corrected.fact(original.reference)
    assert not GraphInputs.from_state(edits[2].state, original.applicability).seeds


def test_wrong_context_is_an_explicit_exclusion_not_a_cross_context_inference(history):
    _, edits = history
    assertion = edits[0].state.assertions.active()[0]
    context = assertion.applicability.model_copy(update={"artifact_id": "different-context"})
    bound = GraphInputs.from_state(edits[0].state, context)
    assert not bound.seeds and bound.excluded_context == (assertion.reference,)


def test_foreign_scope_and_unbound_origins_fail(history):
    _, edits = history
    state = edits[0].state
    context = state.assertions.active()[0].applicability
    foreign = context.model_copy(update={"scope": context.scope.model_copy(update={"project_id": "other"})})
    with pytest.raises(KnowledgeError, match="reasoning_context_scope_mismatch"):
        GraphInputs.from_state(state, foreign)
    with pytest.raises(KnowledgeError, match="reasoning_origin_not_bound"):
        GraphInputs.from_state(state, context).references(("unbound",))
    with pytest.raises(KnowledgeError, match="invalid_reasoning_binding"):
        GraphInputs.from_state(state.to_snapshot(), context)


def test_binding_keeps_all_applicable_conflicting_claims(history):
    fixture, edits = history
    first = edits[0]
    original = first.state.assertions.active()[0]
    opposing = original.model_copy(update={"reference": original.reference.model_copy(update={
        "assertion_id": "opposing"}), "polarity": "negated"})
    proposal = fixture.proposal.model_copy(update={"base": first.head, "change_id": "disagreement",
        "operations": (AddAssertion(operation="add_assertion", assertion=opposing),)})
    second = review(first.state, first.head, proposal)
    bound = GraphInputs.from_state(second.state, original.applicability)
    closure = Evaluator().evaluate(Program("fixture-v1", ()), bound.seeds)
    assert len(bound.seeds) == 2
    assert closure.assess(bound.fact(original.reference)).conflict
    assert closure.assess(bound.fact(original.reference)).status == "unknown"
