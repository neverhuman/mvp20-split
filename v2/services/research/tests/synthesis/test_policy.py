"""Synthesis posture never substitutes for action-specific execution evidence."""
from dataclasses import replace

import pytest
from amphora_research.synthesis.evidence import (
    RouteEvidence,
    RouteProvenance,
    RouteStep,
    SearchRecord,
    SynthesisContext,
)
from amphora_research.synthesis.policy import ExecutionCheck, RouteOption, SynthesisPolicy
from amphora_research.synthesis.validation import SynthesisError

from ..material_state.test_context import CANDIDATE, METHOD, OTHER, artifact, q


def context():
    return SynthesisContext(CANDIDATE,"fixture.polymer","fixture.production",artifact("conditions"),q("1","g"),artifact("purity"))


def route(name="route",posture="demonstrated"):
    return RouteEvidence(context(),artifact(name),posture,RouteProvenance(METHOD,METHOD,(),(artifact("source"),)),
        (RouteStep("prepare",(),posture,artifact("step"),(artifact("step-evidence"),),()),),None,())


def check(name="equipment",status="met"):
    return ExecutionCheck(name,status,(artifact(name+"-evidence"),),("fixture_assertion",))


def policy():
    return SynthesisPolicy(METHOD,context(),("demonstrated",),("demonstrated",),("equipment","precursor_access"))


def option(name="route",status="met"):
    return RouteOption(route(name),(check(status=status),check("precursor_access")))


def test_demonstrated_route_can_be_blocked_without_losing_its_evidence():
    decision = policy().assess(option(status="failed"))
    assert decision.disposition == "blocked" and decision.blockers == ("equipment",)
    assert decision.option.evidence.posture == "demonstrated"


def test_unknown_constraints_are_not_favorable_defaults():
    for checks in ((),(check(status="unknown"),)):
        decision = policy().assess(RouteOption(route(),checks))
        assert decision.disposition == "unknown" and decision.gaps == ("equipment","precursor_access")
    unknown_context = replace(context(),scale=None,purity=None)
    assert unknown_context.scale is None and unknown_context.purity is None


def test_alternatives_are_independent_and_preserve_input_order():
    decisions = policy().assess_alternatives((option("blocked",status="failed"),option("useful")))
    assert [d.disposition for d in decisions] == ["blocked","eligible"]
    assert [d.option.evidence.route.artifact_id for d in decisions] == ["blocked","useful"]
    assert decisions[0].option.checks[0].evidence == (artifact("equipment-evidence"),)


def test_no_route_found_is_bounded_unknown_not_impossibility():
    evidence = RouteEvidence(context(),None,"no_route_found",RouteProvenance(METHOD,METHOD,(),(artifact("search-result"),)),
                             (),SearchRecord(artifact("search-scope"),q("10","attempts")),("broaden_search",))
    decision = policy().assess(RouteOption(evidence,()))
    assert decision.disposition == "unknown" and not decision.blockers
    assert decision.option.evidence.search.budget == q("10","attempts")
    unassessed = RouteEvidence(context(),None,"unassessed",RouteProvenance(METHOD,METHOD,(),()),(),None,())
    assert policy().assess(RouteOption(unassessed,())).disposition == "unknown"


def test_explicit_exploratory_policy_can_use_proposals_without_promoting_them():
    exploratory = replace(policy(),allowed_postures=("proposed",),allowed_step_postures=("proposed",))
    proposal = replace(option(),evidence=route(posture="proposed"))
    assert exploratory.assess(proposal).disposition == "eligible"
    assert policy().assess(proposal).disposition == "unknown"
    assert proposal.evidence.posture == "proposed"


def test_summary_does_not_override_missing_step_evidence():
    evidence = route()
    weak = replace(evidence,steps=(replace(evidence.steps[0],posture="unassessed",sources=(),gaps=("unknown_yield",)),))
    decision = policy().assess(replace(option(),evidence=weak))
    assert decision.disposition == "unknown" and decision.gaps == ("step_evidence:prepare",)
    assert decision.option.evidence.steps[0].gaps == ("unknown_yield",)


def test_failed_required_check_preserves_other_unknowns_and_optional_failures():
    decision = policy().assess(RouteOption(route(),(check(status="failed"),check("optional_cost","unknown"))))
    assert decision.blockers == ("equipment",) and decision.gaps == ("precursor_access",)
    assert decision.option.checks[1].disposition == "unknown"
    optional = replace(option(),checks=option().checks+(check("optional_cost","failed"),))
    assert policy().assess(optional).disposition == "eligible"


def test_ordered_step_dependencies_and_versions_are_retained():
    first = route().steps[0]
    second = replace(first,step_id="purify",requires=(first.step_id,),record=artifact("purify"))
    evidence = replace(route(),steps=(first,second),provenance=RouteProvenance(METHOD,METHOD,(METHOD,),(artifact("source"),)))
    assert evidence.steps[1].requires == ("prepare",) and evidence.provenance.models == (METHOD,)


@pytest.mark.parametrize("factory,reason",[
    (lambda: replace(context(),candidate=None),"synthesis_candidate_required"),
    (lambda: replace(context(),domain=""),"invalid_synthesis_identifier"),
    (lambda: replace(context(),conditions=None),"synthesis_conditions_required"),
    (lambda: replace(context(),scale=1),"synthesis_scale_type"),
    (lambda: replace(context(),scale=q("0","g")),"synthesis_scale_positive"),
    (lambda: replace(context(),purity="pure"),"synthesis_purity_type"),
    (lambda: replace(context(),conditions=artifact(scope=OTHER)),"synthesis_context_scope_mismatch"),
    (lambda: RouteProvenance(None,METHOD,(),()),"route_method_tool_required"),
    (lambda: RouteProvenance(METHOD,METHOD,[],()),"route_model_bound"),
    (lambda: RouteProvenance(METHOD,METHOD,(None,),()),"route_model_bound"),
    (lambda: RouteProvenance(METHOD,METHOD,(METHOD,)*33,()),"route_model_bound"),
    (lambda: RouteProvenance(METHOD,METHOD,(METHOD,)*2,()),"duplicate_route_model"),
    (lambda: RouteProvenance(METHOD,METHOD,(),(artifact(),)*2),"duplicate_route_source"),
    (lambda: replace(route().steps[0],requires=("prepare",)),"route_step_self_dependency"),
    (lambda: replace(route().steps[0],posture="no_route_found"),"invalid_route_step_posture"),
    (lambda: replace(route().steps[0],record=None),"route_step_record_required"),
    (lambda: replace(route().steps[0],sources=()),"route_step_evidence_required"),
    (lambda: SearchRecord(None,q("1","attempts")),"route_search_scope_required"),
    (lambda: SearchRecord(artifact(),q("0","attempts")),"route_search_budget_positive"),
    (lambda: replace(route(),context=None),"synthesis_context_required"),
    (lambda: replace(route(),route="route"),"route_reference_type"),
    (lambda: replace(route(),posture="impossible"),"invalid_route_posture"),
    (lambda: replace(route(),provenance=None),"route_provenance_required"),
    (lambda: replace(route(),search="search"),"route_search_type"),
    (lambda: replace(route(),next_checks=("same","same")),"duplicate_synthesis_reason"),
    (lambda: replace(route(),posture="unassessed"),"absent_route_has_steps"),
    (lambda: replace(route(),route=None),"route_evidence_required"),
    (lambda: RouteEvidence(context(),None,"no_route_found",RouteProvenance(METHOD,METHOD,(),()),(),None,()),"bounded_search_required"),
    (lambda: replace(route(),steps=route().steps*2),"duplicate_route_step"),
    (lambda: replace(route(),steps=(replace(route().steps[0],requires=("future_step",)),)),"route_step_dependency_unresolved"),
    (lambda: replace(route(),route=artifact(scope=OTHER)),"route_evidence_scope_mismatch"),
    (lambda: replace(check(),disposition="good"),"invalid_execution_check"),
    (lambda: replace(check(),evidence=()),"execution_evidence_required"),
    (lambda: replace(check(),reasons=()),"execution_reason_required"),
    (lambda: RouteOption(None,()),"route_evidence_required"),
    (lambda: replace(option(),checks=(check(),check())),"duplicate_execution_check"),
    (lambda: replace(option(),checks=(replace(check(),evidence=(artifact(scope=OTHER),)),)),"execution_evidence_scope_mismatch"),
    (lambda: replace(policy(),reference=None),"synthesis_policy_reference_required"),
    (lambda: replace(policy(),context=None),"synthesis_context_required"),
    (lambda: replace(policy(),allowed_postures=("no_route_found",)),"invalid_allowed_route_posture"),
    (lambda: replace(policy(),allowed_step_postures=()),"invalid_allowed_step_posture"),
    (lambda: replace(policy(),required_checks=()),"explicit_execution_checks_required"),
    (lambda: policy().assess(None),"route_option_required"),
    (lambda: policy().assess(replace(option(),evidence=replace(route(),context=replace(context(),scale=q("100","kg"))))),"route_policy_context_mismatch"),
    (lambda: policy().assess_alternatives(()),"route_options_required"),
    (lambda: policy().assess_alternatives((option(),option())),"duplicate_route_option"),
])
def test_invalid_or_unbound_evidence_is_rejected(factory,reason):
    with pytest.raises(SynthesisError,match=reason):
        factory()
