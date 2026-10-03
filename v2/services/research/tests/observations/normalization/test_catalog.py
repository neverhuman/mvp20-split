"""Independent exact conversion cases; catalog metadata is reviewed, never inferred."""
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest
from amphora_research.observations.normalization.catalog import (
    ConversionCatalog,
    ConversionRule,
    NormalizationUnavailable,
)
from amphora_research.observations.quantities import DecimalValue, MeasurementError, Quantity


def quantity(value, unit="mg"):
    return Quantity(DecimalValue(value),unit)


def catalog():
    return ConversionCatalog("fixture.mass-time","1",(
        ConversionRule("mass","mg","g",DecimalValue("0.001")),
        ConversionRule("mass","g","kg",DecimalValue("0.001")),
        ConversionRule("mass","kg","g",DecimalValue("1000")),
        ConversionRule("time","min","s",DecimalValue("60")),
        ConversionRule("time","h","s",DecimalValue("3600")),
    ))


@pytest.mark.parametrize("source,target,value,expected",[
    ("mg","g","1.2500","0.00125"),("mg","g","-2","-0.002"),("kg","g","1.23","1230"),
    ("min","s","1.5","90"),("h","s","0.5","1800"),("mg","g","-0.000","0"),
    ("mg","g","1234567890123456789012345678901234567890","1234567890123456789012345678901234567.890"),
])
def test_exact_results_ignore_ambient_decimal_precision(source,target,value,expected):
    original = quantity(value,source)
    rule = catalog().select(source,target)
    with localcontext() as context:
        context.prec = 2
        result = rule.apply(original)
    assert result.value.amount == Decimal(expected) and result.unit == target
    assert original.value.text == value and original.unit == source


@pytest.mark.parametrize("source,target,reason",[
    ("mg","s","dimension_mismatch"),("MG","g","unknown_unit"),("unknown","unknown","unknown_unit"),
    ("g","mg","direction_unconfigured"),("mg","kg","direction_unconfigured"),
])
def test_no_implicit_inverse_path_or_name_inference(source,target,reason):
    with pytest.raises(NormalizationUnavailable,match=reason):
        catalog().select(source,target)
    assert catalog().select("g","g") is None


@pytest.mark.parametrize("scale",["0","-1","-0"])
def test_zero_and_negative_scales_cannot_change_censor_orientation(scale):
    with pytest.raises(MeasurementError,match="positive_scale"):
        ConversionRule("mass","mg","g",DecimalValue(scale))


def test_ambiguous_catalogs_and_identity_rules_are_rejected():
    original = catalog()
    with pytest.raises(MeasurementError,match="duplicate_direction"):
        replace(original,rules=original.rules+(original.rules[0],))
    with pytest.raises(MeasurementError,match="dimension_conflict"):
        replace(original,rules=original.rules+(ConversionRule("time","g","minute",DecimalValue("1")),))
    with pytest.raises(MeasurementError,match="identity_rule"):
        ConversionRule("mass","g","g",DecimalValue("1"))
    with pytest.raises(MeasurementError,match="rule_bound"):
        replace(original,rules=())


def test_full_catalog_identity_changes_with_configuration_or_version():
    original = catalog()
    assert catalog().reference == original.reference
    for changed in (replace(original,version="2"),replace(original,profile_id="other"),
        replace(original,rules=tuple(reversed(original.rules))),
        replace(original,rules=(replace(original.rules[0],scale=DecimalValue("0.002")),*original.rules[1:]))):
        assert changed.reference != original.reference


@pytest.mark.parametrize("value,factor",[("1e128","1e128"),("1e-128","1e-128"),("9"*64,"9"*64)])
def test_out_of_bounds_exact_results_are_explicitly_unresolved(value,factor):
    rule = ConversionRule("fixture","from","to",DecimalValue(factor))
    with pytest.raises(NormalizationUnavailable,match="output_bound"):
        rule.apply(quantity(value,"from"))


@pytest.mark.parametrize("factor,expected",[("10","1e129"),("1e63","1e191")])
def test_representable_large_values_are_not_rejected_by_a_preferred_spelling(factor,expected):
    rule = ConversionRule("fixture","from","to",DecimalValue(factor))
    result = rule.apply(quantity("1e128","from"))
    assert result.value.amount == Decimal(expected)
    assert len(result.value.amount.as_tuple().digits) <= 64
