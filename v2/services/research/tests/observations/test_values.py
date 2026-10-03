"""Censoring, uncertainty and missingness preserve reported meaning without a favorable default."""
import pytest
from amphora_research.observations import (
    CategoryValue,
    CensoredValue,
    CensorLimit,
    DecimalValue,
    MeasurementError,
    MissingValue,
    NumericValue,
    Quantity,
    ReportedInterval,
)


def q(value, unit="mg/L"):
    return Quantity(DecimalValue(value),unit)


def test_zero_missing_and_detection_limit_are_distinct_and_uncertainty_stays_unknown():
    point = NumericValue(q("0"))
    missing = MissingValue("not_reported")
    below = CensoredValue(None,CensorLimit(q("0.01"),False))
    assert point.quantity.value.text == "0" and point.uncertainty is None
    assert missing.reason == "not_reported" and not hasattr(missing,"quantity")
    assert below.upper.quantity.value.text == "0.01" and below.lower is None
    assert below.upper.inclusive is False and not hasattr(below,"quantity")
    assert below.unit == "mg/L"


def test_reported_interval_preserves_description_without_invented_confidence():
    interval = ReportedInterval(q("1.0"),q("2.0"),"Reported range; coverage not supplied")
    value = NumericValue(q("1.50"),interval)
    assert value.uncertainty is interval and value.unit == "mg/L"
    assert not hasattr(interval,"confidence")


@pytest.mark.parametrize("factory,reason", [
    (lambda: ReportedInterval(q("2"),q("1"),"reported"),"reversed_uncertainty_interval"),
    (lambda: ReportedInterval(q("1"),q("2","g/L"),"reported"),"measurement_unit_mismatch"),
    (lambda: ReportedInterval("1",q("2"),"reported"),"quantity_required"),
    (lambda: ReportedInterval(q("1"),"2","reported"),"quantity_required"),
    (lambda: NumericValue(q("1","g/L"),ReportedInterval(q("0"),q("2"),"reported")),"measurement_unit_mismatch"),
    (lambda: NumericValue(q("1"),0),"reported_uncertainty_required"),
    (lambda: NumericValue("1"),"quantity_required"),
])
def test_uncertainty_never_coerces_units_or_nonmeasurement_values(factory, reason):
    with pytest.raises(MeasurementError,match=reason):
        factory()


@pytest.mark.parametrize("description", [None, 1, "", " ", "x"*513])
def test_uncertainty_requires_bounded_reported_meaning(description):
    with pytest.raises(MeasurementError,match="uncertainty_description_required"):
        ReportedInterval(q("0"),q("1"),description)


def test_censor_limits_keep_exact_inclusion_and_do_not_become_points_even_if_equal():
    low = CensorLimit(q("1"),True)
    assert CensoredValue(low,None).unit == "mg/L"
    interval = CensoredValue(low,CensorLimit(q("2"),False))
    assert interval.lower.inclusive and not interval.upper.inclusive
    equal = CensoredValue(low,low)
    assert equal.kind == "censored" and not hasattr(equal,"quantity")


@pytest.mark.parametrize("factory,reason", [
    (lambda: CensoredValue(None,None),"censor_limit_required"),
    (lambda: CensoredValue(q("1"),None),"censor_limit_required"),
    (lambda: CensoredValue(None,0),"censor_limit_required"),
    (lambda: CensorLimit("1",True),"quantity_required"),
    (lambda: CensoredValue(CensorLimit(q("2"),True),CensorLimit(q("1"),True)),"empty_censor_interval"),
    (lambda: CensoredValue(CensorLimit(q("1"),False),CensorLimit(q("1"),True)),"empty_censor_interval"),
    (lambda: CensoredValue(CensorLimit(q("1"),True),CensorLimit(q("1"),False)),"empty_censor_interval"),
    (lambda: CensoredValue(CensorLimit(q("1"),True),CensorLimit(q("2","g/L"),True)),"measurement_unit_mismatch"),
])
def test_incoherent_limits_are_rejected_without_fabricated_measurement(factory, reason):
    with pytest.raises(MeasurementError,match=reason):
        factory()


@pytest.mark.parametrize("inclusive", [None, 0, 1, "true"])
def test_limit_inclusion_requires_explicit_boolean(inclusive):
    with pytest.raises(MeasurementError,match="explicit_limit_inclusion_required"):
        CensorLimit(q("1"),inclusive)


def test_category_and_missing_reason_preserve_uninterpreted_text():
    assert CategoryValue("Inconclusive").label == "Inconclusive"
    assert MissingValue("control.not_reported").reason == "control.not_reported"


@pytest.mark.parametrize("label", [None, False, "", " ", "x"*257])
def test_categories_are_bounded(label):
    with pytest.raises(MeasurementError,match="invalid_measurement_category"):
        CategoryValue(label)


@pytest.mark.parametrize("reason", [None, False, "", "no reason", "x"*129])
def test_missing_values_require_stable_reason_codes(reason):
    with pytest.raises(MeasurementError,match="missing_reason_required"):
        MissingValue(reason)
