"""Exact matching preserves weak results; it cannot confer scientific acceptance."""
from dataclasses import FrozenInstanceError, replace

import pytest
from amphora_research.observations import (
    CategoryValue,
    CensoredValue,
    CensorLimit,
    MissingValue,
    NumericValue,
    SeriesPoint,
    SeriesValue,
)
from amphora_research.observations.identity import ObservationError, ObservationIdentity, ObservationReference
from amphora_research.observations.matching import ObservationMatch
from amphora_research.observations.records import (
    MethodClaim,
    Observation,
    ObservationBinding,
    ReportedQuality,
    ReturnTarget,
    SpecimenClaim,
)

from ..experiments.fixtures import experiment
from ..material_state.test_context import OTHER, SCOPE, artifact, q


def observation(plan=None,value=None):
    plan = plan or experiment()
    expected = plan.expectations[0]
    return Observation(ObservationIdentity(ObservationReference(SCOPE,"result",1),None),artifact("report"),
        ObservationBinding(ReturnTarget(plan.identity.reference,expected.expectation_id,expected.replicate.replicate_id),
            SpecimenClaim(expected.sample,plan.samples[0].sample.record.material_state),
            MethodClaim(plan.protocol.method,plan.protocol.applicability),expected.replicate.role),
        value if value is not None else NumericValue(q("1.25","mg/L")),ReportedQuality("unknown",()))


@pytest.mark.parametrize("controls",["unknown","failed","passed"])
def test_matched_quality_is_preserved_without_scientific_promotion(controls):
    result = replace(observation(),quality=ReportedQuality(controls,("questionable","low_accuracy")))
    match = ObservationMatch.reconcile(result,experiment())
    assert match.disposition == "matched" and match.reasons == () and match.state_known
    assert result.quality.controls == controls and result.quality.flags == ("questionable","low_accuracy")
    assert result.value_available


def test_unknown_state_can_match_without_inventing_preparation():
    plan = experiment(False)
    match = ObservationMatch.reconcile(observation(plan),plan)
    assert match.disposition == "matched" and not match.state_known


@pytest.mark.parametrize("field,changed,reason",[
    ("target",lambda b: replace(b.target,experiment=replace(b.target.experiment,revision=2)),"experiment_revision_mismatch"),
    ("target",lambda b: replace(b.target,replicate_id="replicate-2"),"replicate_mismatch"),
    ("target",lambda b: replace(b.target,expectation_id="other"),"unknown_expectation"),
    ("specimen",lambda b: replace(b.specimen,sample=b.specimen.sample.model_copy(update={"revision":2})),"sample_revision_mismatch"),
    ("specimen",lambda b: replace(b.specimen,material_state=b.specimen.material_state.model_copy(update={"material_state_id":"other"})),"material_state_revision_mismatch"),
    ("measurement",lambda b: replace(b.measurement,method=b.measurement.method.model_copy(update={"version":"2"})),"method_mismatch"),
    ("measurement",lambda b: replace(b.measurement,context=artifact("other-context")),"context_mismatch"),
    ("role",lambda b: "blank","control_role_mismatch"),
])
def test_wrong_identity_or_context_is_quarantined_without_rebinding(field,changed,reason):
    original = observation()
    result = replace(original,binding=replace(original.binding,**{field:changed(original.binding)}))
    match = ObservationMatch.reconcile(result,experiment())
    assert match.disposition == "quarantined" and match.reasons == (reason,)
    assert result.source == original.source and result.value == original.value


def test_all_applicable_binding_problems_remain_visible():
    result = replace(observation(),
        identity=ObservationIdentity(ObservationReference(OTHER,"result",1),None),source=artifact(scope=OTHER),
        binding=ObservationBinding(ReturnTarget(None,"readout",None),SpecimenClaim(None,None),MethodClaim(None,None),None),
        value=NumericValue(q("1","g/L")))
    assert ObservationMatch.reconcile(result,experiment()).reasons == (
        "observation_scope_mismatch","experiment_revision_mismatch","method_mismatch","context_mismatch",
        "sample_revision_mismatch","material_state_revision_mismatch","replicate_mismatch","control_role_mismatch",
        "readout_unit_mismatch")


@pytest.mark.parametrize("value,reason",[
    (CategoryValue("positive"),"readout_kind_mismatch"),
    (NumericValue(q("1","g/L")),"readout_unit_mismatch"),
    (CensoredValue(None,CensorLimit(q("1","g/L"),False)),"readout_unit_mismatch"),
])
def test_no_implicit_readout_conversion(value,reason):
    assert ObservationMatch.reconcile(observation(value=value),experiment()).reasons == (reason,)


def test_censoring_missing_and_conflicting_values_remain_separate():
    values = (NumericValue(q("1","mg/L")),NumericValue(q("99","mg/L")),
              CensoredValue(None,CensorLimit(q("0.1","mg/L"),False)),MissingValue("not_reported"))
    results = tuple(observation(value=v) for v in values)
    assert all(ObservationMatch.reconcile(r,experiment()).disposition == "matched" for r in results)
    assert tuple(r.value for r in results) == values
    assert tuple(r.value_available for r in results) == (True,True,True,False)


def test_series_matching_retains_missing_points_and_exact_axes():
    plan = experiment(kind="series",x_unit="s")
    missing = SeriesValue("s","mg/L",(SeriesPoint(q("1","s"),MissingValue("unknown")),))
    result = observation(plan,missing)
    assert ObservationMatch.reconcile(result,plan).disposition == "matched" and not result.value_available
    mixed = replace(missing,points=missing.points+(SeriesPoint(q("2","s"),NumericValue(q("2","mg/L"))),))
    assert observation(plan,mixed).value_available and mixed.reported_count == 1
    wrong = SeriesValue("min","mg/L",(SeriesPoint(q("1","min"),MissingValue("unknown")),))
    assert ObservationMatch.reconcile(observation(plan,wrong),plan).reasons == ("readout_unit_mismatch",)
    category_plan = experiment(kind="categorical",unit=None)
    assert ObservationMatch.reconcile(observation(category_plan,CategoryValue("positive")),category_plan).disposition == "matched"


def test_correction_does_not_mutate_original_quality_or_pending_reference():
    original = observation()
    corrected = replace(original,identity=ObservationIdentity(replace(original.identity.reference,revision=2),original.identity.reference),
                        quality=ReportedQuality("failed",("suspect",)))
    assert corrected.identity.supersedes == original.identity.reference
    assert original.quality.controls == "unknown" and corrected.quality.controls == "failed"
    with pytest.raises(FrozenInstanceError):
        original.quality = corrected.quality


@pytest.mark.parametrize("factory,reason",[
    (lambda: ObservationReference(None,"o",1),"observation_scope_required"),
    (lambda: ObservationReference(SCOPE,"",1),"invalid_observation_identifier"),
    (lambda: ObservationReference(SCOPE,"o",True),"observation_revision_bound"),
    (lambda: ObservationReference(SCOPE,"o",0),"observation_revision_bound"),
    (lambda: ObservationReference(SCOPE,"o",9007199254740992),"observation_revision_bound"),
    (lambda: ObservationIdentity(None,None),"observation_reference_required"),
    (lambda: ObservationIdentity(ObservationReference(SCOPE,"o",2),None),"observation_predecessor_required"),
    (lambda: ObservationIdentity(ObservationReference(SCOPE,"o",2),"o"),"observation_predecessor_type"),
    (lambda: ObservationIdentity(ObservationReference(SCOPE,"o",3),ObservationReference(SCOPE,"o",1)),"observation_predecessor_mismatch"),
    (lambda: ObservationIdentity(ObservationReference(SCOPE,"o",2),ObservationReference(OTHER,"o",1)),"observation_predecessor_mismatch"),
    (lambda: ObservationIdentity(ObservationReference(SCOPE,"o",2),ObservationReference(SCOPE,"other",1)),"observation_predecessor_mismatch"),
    (lambda: ReturnTarget("assay",None,None),"return_experiment_type"),
    (lambda: SpecimenClaim("sample",None),"return_sample_type"),
    (lambda: SpecimenClaim(None,"state"),"return_state_type"),
    (lambda: MethodClaim("method",None),"return_method_type"),
    (lambda: MethodClaim(None,"context"),"return_context_type"),
    (lambda: replace(observation().binding,target=None),"return_target_required"),
    (lambda: replace(observation().binding,specimen=None),"specimen_claim_required"),
    (lambda: replace(observation().binding,measurement=None),"method_claim_required"),
    (lambda: replace(observation().binding,role="unknown"),"return_role_invalid"),
    (lambda: ReportedQuality("acceptable",()),"reported_control_status_invalid"),
    (lambda: ReportedQuality("unknown",[]),"reported_flag_bound"),
    (lambda: ReportedQuality("unknown",("flag",)*65),"reported_flag_bound"),
    (lambda: ReportedQuality("unknown",("flag",)*2),"duplicate_reported_flag"),
    (lambda: replace(observation(),identity=None),"observation_identity_required"),
    (lambda: replace(observation(),source=None),"observation_source_required"),
    (lambda: replace(observation(),source=artifact(scope=OTHER)),"observation_source_scope_mismatch"),
    (lambda: replace(observation(),binding=None),"observation_binding_required"),
    (lambda: replace(observation(),value=0),"observation_value_required"),
    (lambda: replace(observation(),quality=None),"reported_quality_required"),
    (lambda: ObservationMatch.reconcile(None,experiment()),"matching_records_required"),
])
def test_malformed_records_are_not_silently_coerced(factory,reason):
    with pytest.raises(ObservationError,match=reason):
        factory()
