"""Semantic config reconstruction, exact input binding and lossless computed projections."""
import json
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    AssessObservationUseRequest,
    NormalizationTargetRecord,
    NormalizeObservationRequest,
)
from amphora_research.experiments import wire as experiment_wire
from amphora_research.observations import wire as observation_wire
from amphora_research.observations.identity import ObservationError
from amphora_research.observations.interpretation.document import InterpretationDocument, canonical
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.quantities import MeasurementError
from amphora_research.observations.records import ReportedQuality
from amphora_research.observations.values import MissingValue, NumericValue

from ...experiments.fixtures import experiment
from ...material_state.test_context import OTHER, artifact
from ..normalization.test_catalog import catalog, quantity
from ..quality.test_policy import policy
from ..test_matching import observation


def inputs(use=False, strict=False):
    plan = experiment(unit="g")
    row = observation(plan,NumericValue(quantity("1.2500","mg")))
    profile = InterpretationProfile(plan.identity.reference.scope,policy(strict,catalog()) if use else catalog())
    base = dict(wire_version="1",kind=profile.kind,interpretation_id="interpretation-1",profile=profile.reference)
    if use:
        request = AssessObservationUseRequest(**base,experiment=experiment_wire.reference_to_wire(plan.identity.reference),
            observations=(observation_wire.reference_to_wire(row.identity.reference),))
    else:
        request = NormalizeObservationRequest(**base,observation=observation_wire.reference_to_wire(row.identity.reference),
            targets=NormalizationTargetRecord(value_unit="g",coordinate_unit=None))
    return profile,request,row,plan


@pytest.mark.parametrize("use",[False,True])
def test_complete_profiles_roundtrip_and_pin_config_and_scope(use):
    profile,request,_,_ = inputs(use)
    record = profile.to_wire()
    restored = InterpretationProfile.from_wire(type(record).model_validate_json(record.model_dump_json()))
    assert restored == profile and restored.bind(request) == request
    with pytest.raises(ObservationError,match="profile_mismatch"):
        restored.bind(request.model_copy(update={"profile":request.profile.model_copy(update={"scope":OTHER})}))
    with pytest.raises(ObservationError,match="kind_mismatch"):
        restored.bind(inputs(not use)[1])


@pytest.mark.parametrize("field,value",[("scale","0"),("target_unit","mg"),("scale","1e999")])
def test_transport_shape_does_not_bypass_conversion_semantics(field,value):
    profile,_,_,_ = inputs()
    payload = json.loads(profile.to_wire().model_dump_json())
    payload["catalog"]["rules"][0][field] = value
    with pytest.raises(MeasurementError):
        InterpretationProfile.from_wire(type(profile.to_wire()).model_validate_json(json.dumps(payload)))


@pytest.mark.parametrize("use",[False,True])
def test_changed_policy_bytes_with_stale_reference_are_rejected(use):
    profile,_,_,_ = inputs(use)
    payload = json.loads(profile.to_wire().model_dump_json())
    if use:
        payload["policy"]["requirements"]["passed_controls"] = True
    else:
        payload["catalog"]["rules"][0]["scale"] = "0.01"
    with pytest.raises(ObservationError,match="reference_mismatch"):
        InterpretationProfile.from_wire(type(profile.to_wire()).model_validate_json(json.dumps(payload)))


def test_nested_catalog_is_checked_and_optional_catalog_roundtrips():
    profile,_,_,_ = inputs(True)
    payload = json.loads(profile.to_wire().model_dump_json())
    payload["policy"]["normalization"]["rules"][0]["scale"] = "0.01"
    with pytest.raises(ObservationError,match="catalog_reference_mismatch"):
        InterpretationProfile.from_wire(type(profile.to_wire()).model_validate_json(json.dumps(payload)))
    simple = replace(profile,policy=policy())
    assert InterpretationProfile.from_wire(simple.to_wire()) == simple


def test_reference_only_binding_rejects_wrong_scope_and_duplicate_revisions():
    profile,request,_,_ = inputs(True)
    with pytest.raises(ObservationError,match="input_scope_mismatch"):
        profile.bind(request.model_copy(update={"experiment":request.experiment.model_copy(update={"scope":OTHER})}))
    with pytest.raises(ObservationError,match="duplicate_observation"):
        profile.bind(request.model_copy(update={"observations":request.observations*2}))
    profile,request,_,_ = inputs()
    with pytest.raises(ObservationError,match="input_scope_mismatch"):
        profile.bind(request.model_copy(update={"observation":request.observation.model_copy(update={"scope":OTHER})}))


def test_normalized_projection_preserves_lexical_original_and_hashes_all_content():
    profile,request,row,_ = inputs()
    doc = InterpretationDocument.prepare(profile,request,"actor",(row,))
    result = doc.record.result
    assert result.original.quantity.value == "1.2500" and result.normalized.quantity.value == "125e-5"
    assert doc.record.observation.value == result.original and result.status == "normalized"
    assert doc == InterpretationDocument.prepare(profile,request,"actor",(row,))
    changed_actor = InterpretationDocument.prepare(profile,request,"other",(row,))
    assert doc.record.reference != changed_actor.record.reference
    changed_source = InterpretationDocument.prepare(profile,request,"actor",(row,),consumed=(artifact("extra"),))
    assert doc.record.reference != changed_source.record.reference
    unresolved = InterpretationDocument.prepare(profile,request,"actor",(replace(row,value=MissingValue("not_measured")),))
    assert unresolved.record.result.normalized is None and unresolved.record.result.status == "unresolved"


def test_questionable_points_remain_usable_and_visible_under_exploratory_policy():
    profile,request,row,plan = inputs(True)
    row = replace(row,quality=ReportedQuality("failed",("low_accuracy",)))
    doc = InterpretationDocument.prepare(profile,request,"actor",(row,),plan)
    review = doc.record.reviews[0]
    assert review.disposition == "usable" and review.blockers == review.gaps == ()
    assert "controls_failed" in review.focus and "reported_quality_flags" in review.focus
    assert doc.record.usable == doc.record.focus == request.observations
    assert review.raw_match.reasons == ("readout_unit_mismatch",) and not review.effective_match.reasons
    strict,strict_request,_,_ = inputs(True,True)
    excluded = InterpretationDocument.prepare(strict,strict_request,"actor",(row,),plan).record
    assert excluded.reviews[0].disposition == "excluded" and not excluded.usable and excluded.focus


def test_empty_use_batch_retains_missing_coverage_and_context():
    profile,request,_,plan = inputs(True)
    record = InterpretationDocument.prepare(profile,request.model_copy(update={"observations":()}),"actor",(),plan).record
    assert record.missing_expectations == ("readout",) and record.reviews == record.usable == record.focus == ()


def test_projection_binding_never_replaces_requested_inputs():
    for use in (False,True):
        profile,request,row,plan = inputs(use)
        row = replace(row,identity=replace(row.identity,reference=replace(row.identity.reference,observation_id="other")))
        with pytest.raises(ObservationError,match="observation_mismatch"):
            InterpretationDocument.prepare(profile,request,"actor",(row,),plan if use else None)
    with pytest.raises(ObservationError,match="experiment_required"):
        InterpretationDocument.prepare(profile,request,"actor",(row,))


def test_source_identity_conflicts_scope_limits_and_record_byte_bound_fail_closed():
    profile,request,row,_ = inputs()
    for refs,reason in [((row.source.model_copy(update={"size_bytes":row.source.size_bytes+1}),),"source_conflict"),
                        ((row.source.model_copy(update={"scope":OTHER}),),"source_scope"),
                        (tuple(artifact("extra-"+str(n)) for n in range(129)),"source_limit")]:
        with pytest.raises(ObservationError,match=reason):
            InterpretationDocument.prepare(profile,request,"actor",(row,),consumed=refs)
    with pytest.raises(ObservationError,match="byte_limit"):
        canonical({"oversized":"x"*8388608})
