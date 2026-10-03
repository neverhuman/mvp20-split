"""Iteration can continue through weak optional evidence; explicit action gates remain local."""
from dataclasses import replace

import pytest
from amphora_research.eligibility.evidence import (
    CriterionClaim,
    DecisionContext,
    DecisionSubject,
    EligibilityError,
    EvidenceOrigin,
)
from amphora_research.eligibility.policy import EligibilityPolicy, Requirement
from amphora_research.observations.identity import ObservationReference

from ..experiments.fixtures import specimen
from ..material_state.test_context import CANDIDATE, METHOD, OTHER, SCOPE, artifact


def context():
    sample = specimen().sample.record
    return DecisionContext(DecisionSubject(CANDIDATE,sample.material_state,sample.reference),
                           "fixture.polymer","fixture.screening",artifact("conditions"))


def requirement(name="identity",required=True,kind="measurement"):
    return Requirement(name,kind,METHOD,required,())


def policy():
    return EligibilityPolicy(METHOD,context(),(requirement(),requirement("accuracy",False)))


def claim(name="identity",disposition="supported",source="result",kind="measurement"):
    origin = EvidenceOrigin(artifact(source),METHOD,kind,"synthetic",
                            ObservationReference(SCOPE,source,1) if kind == "measurement" else None)
    return CriterionClaim(name,context(),origin,disposition,())


def test_weak_optional_points_do_not_block_progress_and_remain_next_iteration_focus():
    claims = (claim(),replace(claim("accuracy","contradicted","weak"),flags=("low_accuracy","questionable")))
    decision = policy().assess(claims)
    assert decision.disposition == "eligible" and decision.authority == "synthetic"
    assert decision.focus == ("accuracy",)
    assert decision.criteria[1].disposition == "contradicted"
    assert decision.reviews[1].claim.flags == ("low_accuracy","questionable")


def test_explicit_action_gate_is_distinct_from_exploration_gate():
    hard = replace(policy(),requirements=(requirement(),requirement("accuracy",True)))
    claims = (claim(),claim("accuracy","contradicted","weak"))
    assert hard.assess(claims).disposition == "ineligible"
    assert policy().assess(claims).disposition == "eligible"
    assert policy().assess((claim(),)).focus == ("accuracy",)


def test_no_required_prerequisites_is_an_explicit_exploratory_policy():
    exploratory = replace(policy(),requirements=(requirement("accuracy",False),))
    result = exploratory.assess(())
    assert result.disposition == "eligible" and result.focus == ("accuracy",)
    assert result.criteria[0].reason == "missing_eligible_evidence"


def test_missing_required_evidence_is_unknown_not_rejected_or_zero():
    result = policy().assess(())
    assert result.disposition == "unknown" and result.focus == ("identity","accuracy")


def test_contradictions_remain_unknown_without_majority_vote():
    claims = (claim(source="positive-1"),claim(source="positive-2"),claim(disposition="contradicted",source="negative"))
    result = policy().assess(claims)
    assert result.disposition == "unknown" and result.criteria[0].reason == "conflicting_evidence"
    assert len(result.criteria[0].reviews) == 3
    uncertain = policy().assess((claim(),claim(disposition="unknown",source="uncertain")))
    assert uncertain.disposition == "unknown" and uncertain.criteria[0].reason == "explicit_uncertainty"


def test_quality_exclusion_must_be_declared_and_never_erases_the_claim():
    weak = replace(claim(),flags=("failed_controls",))
    permissive = policy().assess((weak,))
    assert permissive.disposition == "eligible" and "identity" in permissive.focus
    strict = replace(policy(),requirements=(replace(requirement(),excluded_flags=("failed_controls",)),))
    result = strict.assess((weak,))
    assert result.disposition == "unknown" and result.reviews[0].reasons == ("quality_excluded_by_policy",)
    assert result.reviews[0].claim is weak


@pytest.mark.parametrize("change",[
    lambda c: replace(c,purpose="fixture.production"),
    lambda c: replace(c,domain="fixture.biological"),
    lambda c: replace(c,conditions=artifact("different-conditions")),
    lambda c: replace(c,subject=replace(c.subject,candidate=CANDIDATE.model_copy(update={"revision":2}))),
    lambda c: replace(c,subject=replace(c.subject,material_state=None)),
    lambda c: replace(c,subject=replace(c.subject,sample=None)),
])
def test_wrong_purpose_domain_target_or_context_cannot_satisfy_a_gate(change):
    result = policy().assess((replace(claim(),context=change(context())),))
    assert result.disposition == "unknown" and result.reviews[0].reasons == ("applicability_mismatch",)


def test_wrong_method_kind_authority_and_undeclared_criteria_are_inspectable():
    wrong = replace(claim(kind="model"),origin=EvidenceOrigin(artifact(),METHOD.model_copy(update={"version":"2"}),"model","scientific"))
    result = policy().assess((wrong,claim("undeclared",source="extra")))
    assert result.disposition == "unknown"
    assert result.reviews[0].reasons == ("authority_mismatch","evidence_kind_mismatch","method_mismatch")
    assert result.reviews[1].reasons == ("undeclared_criterion",)


def test_model_and_route_evidence_need_their_own_declared_requirements():
    for kind in ("model","synthesis"):
        scoped = replace(policy(),requirements=(requirement(kind=kind),))
        result = scoped.assess((claim(kind=kind),))
        assert result.disposition == "eligible" and result.focus == ()
        assert result.reviews[0].claim.origin.kind == kind


def test_corrected_evidence_cannot_change_an_existing_decision():
    original = claim()
    first = policy().assess((original,))
    corrected = replace(original,origin=replace(original.origin,source=artifact("correction"),
                        observation=replace(original.origin.observation,revision=2)),disposition="contradicted")
    later = policy().assess((corrected,))
    assert first.disposition == "eligible" and later.disposition == "ineligible"
    assert first.reviews[0].claim.origin.observation.revision == 1
    assert later.reviews[0].claim.origin.observation.revision == 2


@pytest.mark.parametrize("factory,reason",[
    (lambda: replace(context().subject,candidate=None),"eligibility_candidate_required"),
    (lambda: replace(context().subject,material_state="state"),"eligibility_state_type"),
    (lambda: replace(context().subject,sample="sample"),"eligibility_sample_type"),
    (lambda: replace(context().subject,sample=context().subject.sample.model_copy(update={"scope":OTHER})),"eligibility_subject_scope_mismatch"),
    (lambda: replace(context(),subject=None),"decision_subject_required"),
    (lambda: replace(context(),purpose=""),"invalid_eligibility_identifier"),
    (lambda: replace(context(),conditions=None),"decision_context_required"),
    (lambda: replace(context(),conditions=artifact(scope=OTHER)),"decision_context_scope_mismatch"),
    (lambda: replace(claim().origin,source=None),"eligibility_source_required"),
    (lambda: replace(claim().origin,method=None),"eligibility_method_required"),
    (lambda: replace(claim().origin,kind="truth"),"invalid_eligibility_kind"),
    (lambda: replace(claim().origin,authority="approved"),"invalid_evidence_authority"),
    (lambda: replace(claim().origin,observation="result"),"eligibility_observation_type"),
    (lambda: replace(claim().origin,kind="model"),"eligibility_observation_mismatch"),
    (lambda: replace(claim(),context=None),"decision_context_required"),
    (lambda: replace(claim(),origin=None),"evidence_origin_required"),
    (lambda: replace(claim(),origin=EvidenceOrigin(artifact(scope=OTHER),METHOD,"measurement","synthetic")),"eligibility_source_scope_mismatch"),
    (lambda: replace(claim(),disposition="eligible"),"invalid_criterion_disposition"),
    (lambda: replace(claim(),flags=[]),"eligibility_flag_bound"),
    (lambda: replace(claim(),flags=("flag",)*65),"eligibility_flag_bound"),
    (lambda: replace(claim(),flags=("flag",)*2),"duplicate_eligibility_flag"),
    (lambda: replace(requirement(),kind="truth"),"invalid_eligibility_kind"),
    (lambda: replace(requirement(),method=None),"eligibility_method_required"),
    (lambda: replace(requirement(),required=1),"explicit_requirement_mode_required"),
    (lambda: replace(policy(),reference=None),"eligibility_policy_reference_required"),
    (lambda: replace(policy(),context=None),"decision_context_required"),
    (lambda: replace(policy(),requirements=()),"eligibility_requirement_bound"),
    (lambda: replace(policy(),requirements=(requirement(),)*129),"eligibility_requirement_bound"),
    (lambda: replace(policy(),requirements=(None,)),"eligibility_requirement_required"),
    (lambda: replace(policy(),requirements=(requirement(),)*2),"duplicate_eligibility_requirement"),
    (lambda: policy().assess([]),"eligibility_claim_bound"),
    (lambda: policy().assess((claim(),)*1025),"eligibility_claim_bound"),
    (lambda: policy().assess((None,)),"criterion_claim_required"),
    (lambda: policy().assess((claim(),claim())),"duplicate_criterion_source"),
])
def test_malformed_claims_do_not_acquire_authority(factory,reason):
    with pytest.raises(EligibilityError,match=reason):
        factory()
