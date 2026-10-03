"""Transport round trips preserve reported meaning; domain reconstruction rejects semantic faults."""
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    CensoredMeasurement,
    MeasurementQuantity,
    NumericMeasurement,
    ObservationRevision,
)
from amphora_research.observations import (
    CategoryValue,
    CensoredValue,
    CensorLimit,
    MissingValue,
    NumericValue,
    ReportedInterval,
    SeriesPoint,
    SeriesValue,
    measurement_wire,
    wire,
)
from amphora_research.observations.identity import ObservationIdentity
from amphora_research.observations.quantities import MeasurementError
from amphora_research.observations.records import MethodClaim, ObservationBinding, ReturnTarget, SpecimenClaim

from ..material_state.test_context import q
from .test_matching import observation


@pytest.mark.parametrize("value",[
    NumericValue(q("1.2300e-2","mg/L")),
    NumericValue(q("1","mg/L"),ReportedInterval(q("0.5","mg/L"),q("2","mg/L"),"reported range")),
    CensoredValue(CensorLimit(q("0","mg/L"),True),None),
    CensoredValue(None,CensorLimit(q("1","mg/L"),False)),CategoryValue("reported-positive"),MissingValue("unknown"),
    SeriesValue("s","mg/L",(SeriesPoint(q("2","s"),NumericValue(q("1","mg/L"))),
                            SeriesPoint(q("1","s"),MissingValue("not_reported")))),
])
def test_measurements_survive_json_without_imputation_or_rounding(value):
    encoded = measurement_wire.to_wire(value)
    decoded = type(encoded).model_validate_json(encoded.model_dump_json())
    assert measurement_wire.from_wire(decoded) == value
    record = wire.to_wire(observation(value=value))
    assert wire.from_wire(ObservationRevision.model_validate_json(record.model_dump_json())).value == value


def test_unknown_claims_and_corrections_preserve_exact_history():
    original = observation()
    corrected = replace(original,identity=ObservationIdentity(replace(original.identity.reference,revision=2),original.identity.reference),
                        binding=ObservationBinding(ReturnTarget(None,None,None),SpecimenClaim(None,None),MethodClaim(None,None),None))
    for value in (original,corrected):
        assert wire.from_wire(ObservationRevision.model_validate_json(wire.to_wire(value).model_dump_json())) == value


@pytest.mark.parametrize("record,reason",[
    (NumericMeasurement(kind="numeric",quantity=MeasurementQuantity(value="1e129",unit="g"),uncertainty=None),"decimal_exponent_bound"),
    (NumericMeasurement(kind="numeric",quantity=MeasurementQuantity(value="1"*65,unit="g"),uncertainty=None),"decimal_precision_bound"),
    (CensoredMeasurement(kind="censored",lower=None,upper=None),"censor_limit_required"),
])
def test_shape_success_does_not_bypass_domain_semantics(record,reason):
    with pytest.raises(MeasurementError,match=reason):
        measurement_wire.from_wire(record)


def test_unknown_mapping_input_cannot_be_silently_interpreted():
    with pytest.raises(MeasurementError,match="unsupported_measurement_value"):
        measurement_wire.to_wire(1)
    with pytest.raises(MeasurementError,match="unsupported_measurement_record"):
        measurement_wire.from_wire({"value":1})
