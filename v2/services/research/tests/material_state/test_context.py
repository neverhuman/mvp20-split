"""MAT-01/03/04: same design is not identical preparation or measured morphology."""
from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_research import CandidateRevisionRef, MaterialStateRevisionRef
from amphora_research.material_state.features import FeatureEvidence, MaterialFeature
from amphora_research.material_state.preparation import (
    Condition,
    PreparationHistory,
    ProcessAttribution,
    ProcessingContext,
    ProcessingEvent,
)
from amphora_research.material_state.state import MaterialState, StateIdentity
from amphora_research.material_state.validation import MaterialStateError
from amphora_research.observations import CategoryValue, DecimalValue, MissingValue, NumericValue, Quantity

SCOPE = Scope(tenant_id="fixture",project_id="materials")
OTHER = Scope(tenant_id="fixture",project_id="other")
METHOD = SchemaRef(schema_id="fixture.method",version="1",sha256="a"*64)
CANDIDATE = CandidateRevisionRef(scope=SCOPE,candidate_id="nominal-design",revision=1)


def artifact(name="record", scope=SCOPE):
    return ArtifactRef(artifact_id=name,scope=scope,schema_ref=METHOD,sha256="b"*64,media_type="application/json",size_bytes=2)


def q(value,unit):
    return Quantity(DecimalValue(value),unit)


def event(name="prepare",basis="observed",source=None):
    context = ProcessingContext(METHOD,(Condition("temperature",q("298.15","K")),),q("2.00","min"),None)
    attribution = ProcessAttribution(basis,"operator",None,source or artifact())
    return ProcessingEvent(name,context,attribution)


def identity(name="state",revision=1,prior=None,candidate=CANDIDATE):
    return StateIdentity(MaterialStateRevisionRef(scope=SCOPE,material_state_id=name,revision=revision),candidate,prior)


def feature(name="morphology",basis="measured",source=None):
    return MaterialFeature(name,CategoryValue("reported-form"),FeatureEvidence(basis,METHOD,source or artifact()))


def test_same_nominal_candidate_keeps_distinct_preparation_and_feature_evidence():
    first = MaterialState(identity("first"),PreparationHistory((event("heated"),)),(feature(),))
    proposed = replace(event("quenched",basis="proposed"),context=ProcessingContext(METHOD,(),None,"unreported-gas"))
    second = MaterialState(identity("second"),PreparationHistory((proposed,)),(feature(basis="inferred"),))
    assert first.identity.candidate == second.identity.candidate
    assert first.identity.reference != second.identity.reference and first != second
    assert first.preparation.posture == "observed" and second.preparation.posture == "proposed"
    assert first.features[0].evidence.basis == "measured" and second.features[0].evidence.basis == "inferred"


def test_order_conditions_duration_and_unknown_equipment_atmosphere_remain_original():
    events = (event("heat"),event("quench"))
    history = PreparationHistory(events)
    assert history.events is events and [item.event_id for item in history.events] == ["heat","quench"]
    assert history.events[0].context.duration == q("2.00","min")
    assert history.events[0].context.conditions[0].quantity == q("298.15","K")
    assert history.events[0].context.atmosphere is None and history.events[0].attribution.equipment is None
    assert replace(history.events[0].attribution,equipment=()).equipment == ()
    with pytest.raises(FrozenInstanceError):
        history.events = tuple(reversed(events))


def test_unknown_preparation_and_morphology_do_not_become_observed_or_zero():
    unknown = MaterialFeature("morphology",MissingValue("not_characterized"),FeatureEvidence("unknown",None,None))
    state = MaterialState(identity(),PreparationHistory(()),(unknown,))
    assert state.preparation.posture == "unknown"
    assert state.features[0].value.kind == "missing" and state.features[0].evidence.source is None
    mixed = PreparationHistory((event("plan","proposed"),event("observed","observed")))
    assert mixed.posture == "mixed"


def test_correction_keeps_original_state_and_explicit_predecessor():
    original = MaterialState(identity(),PreparationHistory((event(),)),(feature(),))
    corrected = MaterialState(identity(revision=2,prior=original.identity.reference),PreparationHistory(()),())
    assert corrected.identity.supersedes == original.identity.reference
    assert original.preparation.posture == "observed" and corrected.preparation.posture == "unknown"


def test_empty_series_cannot_claim_measured_morphology():
    from amphora_research.observations import SeriesPoint, SeriesValue

    missing = SeriesValue("s","nm",(SeriesPoint(q("1","s"),MissingValue("not_characterized")),))
    with pytest.raises(MaterialStateError,match="feature_series_has_no_reported_values"):
        MaterialFeature("morphology",missing,FeatureEvidence("measured",METHOD,artifact()))
    mixed = replace(missing,points=missing.points+(SeriesPoint(q("2","s"),NumericValue(q("2","nm"))),))
    assert MaterialFeature("morphology",mixed,FeatureEvidence("measured",METHOD,artifact())).value.reported_count == 1


@pytest.mark.parametrize("factory,reason", [
    (lambda: identity(revision=2),"state_predecessor_required"),
    (lambda: identity(revision=2,prior=identity("other").reference),"state_predecessor_mismatch"),
    (lambda: identity(revision=3,prior=identity().reference),"state_predecessor_mismatch"),
    (lambda: identity(prior="state"),"state_predecessor_type"),
    (lambda: identity(candidate=CANDIDATE.model_copy(update={"scope":OTHER})),"state_candidate_scope_mismatch"),
    (lambda: StateIdentity("state",CANDIDATE,None),"state_reference_required"),
    (lambda: MaterialState("state",PreparationHistory(()),()),"state_identity_required"),
    (lambda: MaterialState(identity(),(),()),"preparation_history_required"),
    (lambda: MaterialState(identity(),PreparationHistory((event(source=artifact(scope=OTHER)),)),()),"material_source_scope_mismatch"),
    (lambda: MaterialState(identity(),PreparationHistory(()),(feature(source=artifact(scope=OTHER)),)),"material_source_scope_mismatch"),
])
def test_state_identity_and_source_scope_never_reconcile_implicitly(factory,reason):
    with pytest.raises(MaterialStateError,match=reason):
        factory()


@pytest.mark.parametrize("factory,reason", [
    (lambda: Condition("invalid condition",q("1","K")),"invalid_state_identifier"),
    (lambda: Condition("temperature",1),"condition_quantity_required"),
    (lambda: ProcessingContext("method",(),None,None),"processing_method_required"),
    (lambda: ProcessingContext(METHOD,[],None,None),"condition_bound"),
    (lambda: ProcessingContext(METHOD,(None,),None,None),"condition_required"),
    (lambda: ProcessingContext(METHOD,(Condition("x",q("1","1")),)*2,None,None),"duplicate_condition"),
    (lambda: ProcessingContext(METHOD,(),"1",None),"duration_quantity_required"),
    (lambda: ProcessingContext(METHOD,(),q("-1","s"),None),"negative_processing_duration"),
    (lambda: ProcessingContext(METHOD,(),None," "),"invalid_atmosphere"),
    (lambda: ProcessAttribution("assumed","operator",None,artifact()),"invalid_preparation_basis"),
    (lambda: ProcessAttribution("observed","operator",None,"source"),"processing_source_required"),
    (lambda: ProcessAttribution("observed","operator",[],artifact()),"equipment_bound"),
    (lambda: ProcessAttribution("observed","operator",("same","same"),artifact()),"duplicate_equipment"),
    (lambda: ProcessAttribution("observed","operator",("invalid equipment",),artifact()),"invalid_state_identifier"),
    (lambda: ProcessingEvent("step",None,event().attribution),"processing_context_required"),
    (lambda: ProcessingEvent("step",event().context,None),"processing_attribution_required"),
    (lambda: PreparationHistory([]),"processing_event_bound"),
    (lambda: PreparationHistory((None,)),"processing_event_required"),
    (lambda: PreparationHistory((event(),event())),"duplicate_processing_event"),
])
def test_processing_rejects_ambiguous_or_malformed_structure_without_guessing(factory,reason):
    with pytest.raises(MaterialStateError,match=reason):
        factory()


@pytest.mark.parametrize("factory,reason", [
    (lambda: FeatureEvidence("assumed",None,None),"invalid_feature_basis"),
    (lambda: FeatureEvidence("unknown","method",None),"feature_method_type"),
    (lambda: FeatureEvidence("unknown",None,"source"),"feature_source_type"),
    (lambda: FeatureEvidence("measured",None,artifact()),"feature_evidence_required"),
    (lambda: FeatureEvidence("inferred",METHOD,None),"feature_evidence_required"),
    (lambda: MaterialFeature("x",0,FeatureEvidence("unknown",None,None)),"feature_value_required"),
    (lambda: MaterialFeature("x",CategoryValue("x"),None),"feature_attribution_required"),
    (lambda: MaterialFeature("x",MissingValue("missing"),FeatureEvidence("measured",METHOD,artifact())),"feature_basis_value_mismatch"),
    (lambda: MaterialFeature("x",NumericValue(q("0","1")),FeatureEvidence("unknown",None,None)),"feature_basis_value_mismatch"),
    (lambda: MaterialState(identity(),PreparationHistory(()),[]),"material_feature_bound"),
    (lambda: MaterialState(identity(),PreparationHistory(()),(None,)),"material_feature_required"),
    (lambda: MaterialState(identity(),PreparationHistory(()),(feature(),feature())),"duplicate_material_feature"),
])
def test_feature_posture_and_sources_are_explicit(factory,reason):
    with pytest.raises(MaterialStateError,match=reason):
        factory()


def test_processing_and_feature_collections_have_finite_resource_bounds():
    with pytest.raises(MaterialStateError,match="condition_bound"):
        ProcessingContext(METHOD,tuple(Condition("c"+str(i),q("1","1")) for i in range(65)),None,None)
    with pytest.raises(MaterialStateError,match="equipment_bound"):
        ProcessAttribution("observed","operator",tuple("e"+str(i) for i in range(33)),artifact())
    with pytest.raises(MaterialStateError,match="processing_event_bound"):
        PreparationHistory(tuple(event("e"+str(i)) for i in range(257)))
    with pytest.raises(MaterialStateError,match="material_feature_bound"):
        MaterialState(identity(),PreparationHistory(()),tuple(feature("f"+str(i)) for i in range(129)))
