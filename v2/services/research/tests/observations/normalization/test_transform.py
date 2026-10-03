"""Normalization preserves evidence meaning, not just numeric equality."""
from decimal import Decimal

import pytest
from amphora_research.observations.normalization.transform import NormalizationTargets, NormalizedMeasurement
from amphora_research.observations.quantities import MeasurementError
from amphora_research.observations.series import SeriesPoint, SeriesValue
from amphora_research.observations.values import (
    CategoryValue,
    CensoredValue,
    CensorLimit,
    MissingValue,
    NumericValue,
    ReportedInterval,
)

from .test_catalog import catalog, quantity


def normalize(value, target="g", coordinate=None):
    return NormalizedMeasurement.evaluate(catalog(),value,NormalizationTargets(target,coordinate))


def test_uncertainty_and_original_lexical_value_are_preserved():
    value = NumericValue(quantity("1.2500"),ReportedInterval(quantity("1.20"),quantity("1.30"),"reported interval, method unspecified"))
    result = normalize(value)
    assert result.status == "normalized" and result.original is value and result.policy == catalog().reference
    assert result.normalized.quantity.value.amount == Decimal("0.00125")
    assert result.normalized.uncertainty.lower.value.amount == Decimal("0.0012")
    assert result.normalized.uncertainty.upper.value.amount == Decimal("0.0013")
    assert result.normalized.uncertainty.description == value.uncertainty.description
    assert result.original.quantity.value.text == "1.2500"
    assert result.applied == (catalog().rules[0],) and result.reason is None


@pytest.mark.parametrize("lower,upper",[(None,CensorLimit(quantity("0.01"),False)),
    (CensorLimit(quantity("-2"),True),None),(CensorLimit(quantity("1"),False),CensorLimit(quantity("2"),True))])
def test_censored_bounds_remain_censored_with_original_inclusion(lower,upper):
    value = CensoredValue(lower,upper)
    result = normalize(value)
    assert type(result.normalized) is CensoredValue and result.original is value
    for before,after in ((lower,result.normalized.lower),(upper,result.normalized.upper)):
        if before is None:
            assert after is None
        else:
            assert after.inclusive is before.inclusive and after.quantity.unit == "g"
    if lower is not None and upper is not None:
        assert result.normalized.lower.quantity.value.amount == Decimal("0.001")
        assert result.normalized.upper.quantity.value.amount == Decimal("0.002")


def test_series_keeps_order_duplicates_missingness_and_optional_coordinates():
    points = (SeriesPoint(quantity("2","min"),NumericValue(quantity("1"))),
        SeriesPoint(quantity("1","min"),MissingValue("instrument_failure")),
        SeriesPoint(quantity("2","min"),CensoredValue(None,CensorLimit(quantity("2"),False))))
    series = SeriesValue("min","mg",points)
    result = normalize(series,coordinate="s")
    assert [p.x.value.amount for p in result.normalized.points] == [Decimal("120"),Decimal("60"),Decimal("120")]
    assert result.normalized.points[1].y is points[1].y
    assert type(result.normalized.points[2].y) is CensoredValue
    assert result.normalized.reported_count == series.reported_count == 2
    retained = normalize(series)
    assert tuple(p.x for p in retained.normalized.points) == tuple(p.x for p in points)
    assert retained.normalized.x_unit == "min" and retained.original == series


def test_one_bad_conversion_does_not_expose_partial_series():
    series = SeriesValue("s","kg",(SeriesPoint(quantity("1","s"),NumericValue(quantity("1","kg"))),
        SeriesPoint(quantity("2","s"),NumericValue(quantity("9"*64+"e128","kg")))))
    result = normalize(series)
    assert result.status == "unresolved" and result.reason == "normalization_output_bound"
    assert result.normalized is None and result.applied == () and result.original is series


@pytest.mark.parametrize("value,target,coordinate,reason",[
    (MissingValue("not_reported"),"g",None,"normalization_missing"),
    (CategoryValue("opaque"),"g",None,"normalization_categorical"),
    (NumericValue(quantity("1","unknown")),"g",None,"normalization_unknown_unit"),
    (NumericValue(quantity("1")),"s",None,"normalization_dimension_mismatch"),
    (NumericValue(quantity("1")),"g","s","normalization_coordinate_requires_series"),
])
def test_unresolved_is_not_zero_or_discarded_source(value,target,coordinate,reason):
    result = normalize(value,target,coordinate)
    assert result.status == "unresolved" and result.reason == reason
    assert result.normalized is None and result.original is value and not result.applied


def test_identity_transform_keeps_existing_precision_text():
    value = NumericValue(quantity("1.000","g"))
    result = normalize(value)
    assert result.normalized is value and result.applied == ()


def test_non_measurements_are_configuration_errors_not_unresolved_science():
    with pytest.raises(MeasurementError,match="measurement_required"):
        normalize(1)
