import json

import pytest
from amphora_contracts_knowledge import (
    GroundLiteral,
    GroundRule,
    ReasoningLimits,
    ReasoningRequest,
    ReasoningRuleSet,
)
from amphora_knowledge.access import Principal
from amphora_knowledge.authoring.canonical import KnowledgeError, canonical
from amphora_knowledge.reasoning.profile import RuleProfile
from pydantic import ValidationError

from ..replay.test_chain import history as history


@pytest.fixture
def configured(history):
    _, edits = history
    state = edits[0].state
    claim = state.assertions.active()[0]
    literal = GroundLiteral(subject=claim.subject, predicate=claim.predicate, object=claim.object, polarity=claim.polarity)
    profile = RuleProfile(ReasoningRuleSet(wire_version="1", graph=state.graph, rule_set_id="fixture", version="v1",
        authority="synthetic_logical_entailment", context=claim.applicability,
        limits=ReasoningLimits(depth=32, work=100_000, facts=8192), rules=()))
    request = ReasoningRequest(wire_version="1", request_id="reason", snapshot=state.reference,
        rule_set=profile.reference, context=claim.applicability, subject=claim.applicability,
        purpose="fixture_support", targets=(literal,))
    principal = Principal("fixture", state.graph.scope, frozenset({"reason_graph"}))
    return profile, principal, state, request


def test_exact_bound_result_projects_without_scientific_promotion(configured):
    profile, principal, state, request = configured
    result = profile.evaluate(principal, state, request).to_record()
    assert result.request == request and result.authority == "synthetic_logical_entailment"
    assert result.outcome.status == "complete" and result.work == 0
    finding = result.findings[0]
    assert finding.status == "supported" and not finding.conflict
    assert finding.supporting_assertions == (state.assertions.active()[0].reference,)
    assert result.steps[0].rule_id is None and result.steps[0].depth == 0
    assert json.loads(canonical(result))["request"]["snapshot"]["sha256"] == state.reference.sha256


def test_explicit_rule_derivation_and_original_premise_projection(configured):
    original, principal, state, request = configured
    premise = request.targets[0]
    opposite = premise.model_copy(update={"polarity": "negated"})
    profile = RuleProfile(original.record.model_copy(update={"rules": (
        GroundRule(rule_id="synthetic_conflict", premises=(premise,), conclusion=opposite),)}))
    request = request.model_copy(update={"rule_set": profile.reference})
    result = profile.evaluate(principal, state, request).to_record()
    finding = result.findings[0]
    assert finding.status == "unknown" and finding.conflict
    assert finding.supporting_assertions == finding.opposing_assertions
    derived = next(step for step in result.steps if step.rule_id is not None)
    assert derived.depth == 1 and derived.premises == (premise,) and derived.assertions == ()


def test_changed_limits_change_pin_and_incomplete_cannot_support(configured):
    original, principal, state, request = configured
    premise = request.targets[0]
    opposite = premise.model_copy(update={"polarity": "negated"})
    profile = RuleProfile(original.record.model_copy(update={"limits": ReasoningLimits(depth=1, work=1, facts=1),
        "rules": (GroundRule(rule_id="r", premises=(premise,), conclusion=opposite),)}))
    assert profile.reference != original.reference
    result = profile.evaluate(principal, state, request.model_copy(update={"rule_set": profile.reference})).to_record()
    assert result.outcome.code == "reasoning_work_limit" and result.findings[0].status == "unknown"


@pytest.mark.parametrize("variant,code", [("snapshot", "reasoning_snapshot_mismatch"),
    ("profile", "reasoning_profile_mismatch"), ("context", "reasoning_applicability_mismatch"),
    ("subject", "reasoning_applicability_mismatch"), ("duplicate", "duplicate_reasoning_target"),
    ("foreign_literal", "reasoning_literal_graph_mismatch"), ("predicate", "unknown_predicate"),
    ("permission", "access_denied")])
def test_request_cannot_change_owner_pins_or_authority(configured, variant, code):
    profile, principal, state, request = configured
    if variant == "snapshot":
        request = request.model_copy(update={"snapshot": request.snapshot.model_copy(update={"sha256": "0"*64})})
    elif variant == "profile":
        request = request.model_copy(update={"rule_set": request.rule_set.model_copy(update={"sha256": "0"*64})})
    elif variant == "context":
        request = request.model_copy(update={"context": request.context.model_copy(update={"artifact_id": "other"})})
    elif variant == "subject":
        request = request.model_copy(update={"subject": request.subject.model_copy(update={"scope":
            request.subject.scope.model_copy(update={"project_id": "other"})})})
    elif variant == "duplicate":
        request = request.model_copy(update={"targets": request.targets * 2})
    elif variant == "foreign_literal":
        target = request.targets[0]
        target = target.model_copy(update={"subject": target.subject.model_copy(update={"graph":
            target.subject.graph.model_copy(update={"graph_id": "other"})})})
        request = request.model_copy(update={"targets": (target,)})
    elif variant == "predicate":
        request = request.model_copy(update={"targets": (request.targets[0].model_copy(update={"predicate": "invented"}),)})
    else:
        principal = Principal("fixture", state.graph.scope, frozenset({"read_graph"}))
    with pytest.raises(KnowledgeError, match=code):
        profile.evaluate(principal, state, request)


def test_constructed_boolean_cannot_be_normalized_into_valid_budget(configured):
    profile, _, _, _ = configured
    invalid = profile.record.model_copy(update={"limits": profile.record.limits.model_copy(update={"depth": True})})
    with pytest.raises(ValidationError):
        RuleProfile(invalid)


def test_foreign_profile_is_rejected_even_before_evaluation(configured):
    profile, _, _, request = configured
    foreign_context = request.context.model_copy(update={"scope": request.context.scope.model_copy(update={"project_id": "other"})})
    with pytest.raises(KnowledgeError, match="reasoning_profile_scope_mismatch"):
        RuleProfile(profile.record.model_copy(update={"context": foreign_context}))


def test_repeated_explanations_are_bounded_before_serializing_large_output(configured, monkeypatch):
    from amphora_knowledge.reasoning import projection

    profile, principal, state, request = configured
    # One reference in the finding plus the same reference in the seed proof is two
    # serialized occurrences, even though both name the same immutable assertion.
    monkeypatch.setattr(projection, "MAX_EXPLANATION_REFERENCES", 1)
    with pytest.raises(KnowledgeError, match="reasoning_explanation_limit"):
        profile.evaluate(principal, state, request).to_record()
