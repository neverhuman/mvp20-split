"""Reviewed full configuration, exact report pins and authenticated scope bind before any I/O."""
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    EligibilityInputProfile,
    ScientificAssessmentRequest,
    SynthesisInputProfile,
)
from amphora_research.eligibility.wire import profile_to_wire
from amphora_research.scientific_api.boundary import ConfiguredScientificInput, ScientificInputError
from amphora_research.synthesis.wire import profile_to_wire as synthesis_wire
from pydantic import ValidationError

from ..eligibility.test_policy import policy
from ..material_state.test_context import METHOD, OTHER, artifact
from ..synthesis.test_policy import policy as synthesis_policy


def profile_case(kind="eligibility"):
    if kind == "eligibility":
        document = EligibilityInputProfile(wire_version="1",kind=kind,profile_id="screening",version="1",
            policy=profile_to_wire(policy()),adapter=METHOD,publishers=("fixture",))
    else:
        document = SynthesisInputProfile(wire_version="1",kind=kind,profile_id="routes",version="1",
            policy=synthesis_wire(synthesis_policy()),adapter=METHOD,publishers=("fixture",))
    configured = ConfiguredScientificInput(document)
    request = ScientificAssessmentRequest(wire_version="1",decision_id="decision",profile=configured.reference,reports=(artifact("report"),))
    return configured,request


@pytest.mark.parametrize("kind",["eligibility","synthesis"])
def test_exact_profile_and_request_are_bound_without_rewriting_original_configuration(kind):
    configured,request = profile_case(kind)
    bound = configured.bind(request,"fixture",configured.scope)
    assert bound.request == request and bound.actor == "fixture"
    assert bound.key == {"tenant":configured.scope.tenant_id,"project":configured.scope.project_id,"kind":kind,"id":"decision"}
    assert ConfiguredScientificInput(configured.document).reference == configured.reference


@pytest.mark.parametrize("change",[
    lambda d:d.model_copy(update={"publishers":("another",)}),
    lambda d:d.model_copy(update={"adapter":d.adapter.model_copy(update={"sha256":"0"*64})}),
    lambda d:d.model_copy(update={"policy":d.policy.model_copy(update={"requirements":d.policy.requirements[:1]})}),
])
def test_full_profile_digest_changes_even_if_label_and_version_are_reused(change):
    configured,_ = profile_case()
    changed = ConfiguredScientificInput(change(configured.document))
    assert changed.reference.profile_id == configured.reference.profile_id and changed.reference.version == configured.reference.version
    assert changed.reference.sha256 != configured.reference.sha256


@pytest.mark.parametrize("change,reason",[
    (lambda r:r.model_copy(update={"profile":r.profile.model_copy(update={"sha256":"0"*64})}),"scientific_input_profile_mismatch"),
    (lambda r:r.model_copy(update={"profile":r.profile.model_copy(update={"kind":"synthesis"})}),"scientific_input_profile_mismatch"),
    (lambda r:r.model_copy(update={"profile":r.profile.model_copy(update={"scope":OTHER})}),"scientific_input_scope_mismatch"),
    (lambda r:r.model_copy(update={"reports":(r.reports[0].model_copy(update={"scope":OTHER}),)}),"scientific_input_report_scope"),
    (lambda r:r.model_copy(update={"reports":r.reports*2}),"scientific_input_duplicate_report"),
])
def test_changed_or_foreign_request_cannot_bind(change,reason):
    configured,request = profile_case()
    with pytest.raises(ScientificInputError,match=reason):
        configured.bind(change(request),"fixture",configured.scope)


def test_config_and_unsafe_boundary_copies_are_revalidated():
    configured,request = profile_case()
    with pytest.raises(ScientificInputError,match="duplicate_publisher"):
        ConfiguredScientificInput(configured.document.model_copy(update={"publishers":("fixture","fixture")}))
    with pytest.raises(ValidationError):
        configured.bind(request.model_copy(update={"reports":()}),"fixture",configured.scope)
    with pytest.raises(ValidationError):
        configured.bind(request,"invalid actor",configured.scope)
    with pytest.raises(ScientificInputError,match="scope_mismatch"):
        configured.bind(request,"fixture",OTHER)


def test_private_policy_reconstruction_keeps_exploratory_vs_action_prerequisites():
    configured,_ = profile_case()
    assert not configured.policy.requirements[1].required
    changed = replace(configured.policy,requirements=(replace(configured.policy.requirements[0],required=False),))
    exploratory = ConfiguredScientificInput(configured.document.model_copy(update={"policy":profile_to_wire(changed)}))
    assert exploratory.policy.assess(()).disposition == "eligible"
    assert exploratory.policy.assess(()).focus == ("identity",)
