"""Exact lab values retain lexical provenance and reject implicit float/boolean coercion."""
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext

import pytest
from amphora_research.observations import DecimalValue, MeasurementError, Quantity


@pytest.mark.parametrize("text", ["0", "-0.00", "1.00", "0.000001", "-2.5E+3", "1e-128", "1E128", "9"*64])
def test_exact_original_text_is_independent_of_decimal_arithmetic_context(text):
    with localcontext() as context:
        context.prec = 2
        value = DecimalValue(text)
        assert value.text == text and value.amount == Decimal(text)
    with pytest.raises(FrozenInstanceError):
        value.text = "0"


def test_equal_amounts_do_not_discard_original_reported_precision_or_unit_spelling():
    first, second = DecimalValue("1.00"), DecimalValue("1e0")
    assert first.amount == second.amount and first != second
    assert Quantity(first,"mg/L").unit == "mg/L"
    assert Quantity(first,"unknown-unit").unit == "unknown-unit"


@pytest.mark.parametrize("value", [0, 1.2, True, None, Decimal("1"), "", " 1", "1 ", "+1", "01", ".1", "1.",
                                      "1,000", "NaN", "Infinity", "-Infinity", "1e", "1\n", "1"*129])
def test_decimal_input_never_guesses_or_coerces(value):
    with pytest.raises(MeasurementError, match="invalid_decimal_text"):
        DecimalValue(value)


@pytest.mark.parametrize("value,reason", [("1e129","decimal_exponent_bound"), ("1e-129","decimal_exponent_bound"),
    ("1e"+"9"*100,"decimal_exponent_bound"), ("1"*65,"decimal_precision_bound"),
    ("1.0e-128","decimal_precision_bound")])
def test_decimal_resource_limits_fail_without_rounding(value, reason):
    with pytest.raises(MeasurementError, match=reason):
        DecimalValue(value)


@pytest.mark.parametrize("unit", [None, 1, True, "", "mg L", "mg\n", "\x00", "a"*33])
def test_unit_is_explicit_bounded_opaque_text(unit):
    with pytest.raises(MeasurementError, match="invalid_measurement_unit"):
        Quantity(DecimalValue("1"),unit)


@pytest.mark.parametrize("value", [1, 1.2, Decimal("1"), "1", True])
def test_quantity_requires_an_explicit_exact_value(value):
    with pytest.raises(MeasurementError, match="exact_decimal_required"):
        Quantity(value,"g")
