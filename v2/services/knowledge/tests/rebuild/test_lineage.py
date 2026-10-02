"""Independent structural lineage oracles; observations are synthetic fixtures."""

from amphora_contracts_knowledge import AddAssertion, CorrectAssertion, MergeEntities, RetractAssertion

from ..persistence.test_ledger import observation
from .test_publication import rebuild as rebuild


def accept(case, identity, operations, **updates):
    head = case.ledger.head(case.principal, case.proposal.graph)
    proposal = case.proposal.model_copy(update={"change_id": identity, "base": head,
        "operations": tuple(operations), **updates})
    receipt = case.ledger.accept(case.principal, proposal, observation(proposal))
    assert receipt.decision.outcome == "accepted"
    return proposal, receipt.decision.head


def test_qev02_trace04_correction_preserves_both_interpretations_and_override(rebuild):
    case = rebuild
    original = case.proposal.operations[2].assertion
    trace = original.grounding.conversion_traces[0].model_copy(update={"trace_id": "corrected-interpretation", "sha256": "e"*64})
    grounding = original.grounding.model_copy(update={"conversion_traces": (trace,),
        "interpretation_artifacts": (original.applicability.model_copy(update={"artifact_id": "override-context"}),)})
    corrected = original.model_copy(update={"reference": original.reference.model_copy(update={"revision": 2}),
        "supersedes": original.reference, "polarity": "negated", "grounding": grounding})
    proposal, head = accept(case, "attributed-correction", [CorrectAssertion(operation="correct_assertion",
        prior=original.reference, replacement=corrected)], description="Human-authored override for the next campaign",
        rationale="Preserve the original interpretation; correct its relationship.")
    result = case.workflow.run(case.principal, case.proposal.graph, "trace-rebuild")
    assert result.result_head == head
    snapshot = case.ledger.snapshot(case.principal, head.snapshot)
    first, second = snapshot.content.assertions
    assert (first.reference.revision, second.reference.revision) == (1, 2)
    assert first.grounding == original.grounding and second.grounding == grounding
    assert first.research_links == second.research_links == original.research_links
    assert second.supersedes == first.reference
    record = case.ledger.change(case.principal, head.change)
    assert record.content.proposal.description == proposal.description
    assert record.content.proposal.rationale == proposal.rationale
    assert record.content.actor_id == case.principal.actor_id


def test_qev03_incompatible_answers_methods_and_contexts_remain_distinct(rebuild):
    case = rebuild
    first = case.proposal.operations[2].assertion
    method = first.research_links[0].validation_method.model_copy(update={"schema_id": "alternative-method", "sha256": "e"*64})
    alternative = first.model_copy(update={"reference": first.reference.model_copy(update={"assertion_id": "alternative"}),
        "polarity": "negated", "applicability": first.applicability.model_copy(update={"artifact_id": "other-context"}),
        "research_links": (first.research_links[0].model_copy(update={"role": "contradiction", "validation_method": method}),)})
    _, head = accept(case, "incompatible-answer", [AddAssertion(operation="add_assertion", assertion=alternative)])
    assert case.workflow.run(case.principal, case.proposal.graph, "answers").result_head == head
    assertions = {record.reference.assertion_id: record for record in case.ledger.snapshot(case.principal, head.snapshot).content.assertions}
    assert set(assertions) == {"claim", "alternative"}
    assert assertions["claim"] == first and assertions["alternative"] == alternative
    assert {record.posture for record in assertions.values()} == {"hypothesis"}


def test_qev04_stale_graph_and_foreign_question_fail_without_log_advancement(rebuild):
    case = rebuild
    first = case.proposal.operations[2].assertion
    _, current = accept(case, "retract", [RetractAssertion(operation="retract_assertion", assertion=first.reference)])
    stale = case.proposal.model_copy(update={"change_id": "stale", "base": case.receipt.decision.head})
    receipt = case.ledger.accept(case.principal, stale, observation(stale))
    assert receipt.decision.outcome == "conflict"
    foreign = first.research_links[0].question.model_copy(update={"scope": first.reference.graph.scope.model_copy(update={"project_id": "foreign"})})
    claim = first.model_copy(update={"reference": first.reference.model_copy(update={"assertion_id": "foreign-claim"}),
        "research_links": (first.research_links[0].model_copy(update={"question": foreign}),)})
    proposal = case.proposal.model_copy(update={"change_id": "foreign", "base": current,
        "operations": (AddAssertion(operation="add_assertion", assertion=claim),)})
    rejected = case.ledger.accept(case.principal, proposal, observation(case.proposal))
    assert rejected.decision.outcome == "rejected"
    assert rejected.decision.findings[0].code == "reference_scope_mismatch"
    assert case.workflow.run(case.principal, case.proposal.graph, "unchanged").result_head == current


def test_merge_and_retraction_rebuild_keep_original_ids_and_history(rebuild):
    case = rebuild
    left, right = [item.entity.reference for item in case.proposal.operations[:2]]
    claim = case.proposal.operations[2].assertion
    _, head = accept(case, "merge-retract", [MergeEntities(operation="merge_entities", source=left, target=right),
        RetractAssertion(operation="retract_assertion", assertion=claim.reference)])
    case.workflow.run(case.principal, case.proposal.graph, "aliases")
    snapshot = case.ledger.snapshot(case.principal, head.snapshot)
    assert [record.reference.entity_id for record in snapshot.content.entities] == ["A", "B"]
    assert snapshot.content.aliases[0].source == left and snapshot.content.aliases[0].target == right
    assert snapshot.content.assertions == (claim,)
    assert snapshot.content.retractions[0].assertion == claim.reference
