"""Transport/schema parity for exact-text values, independent of scientific semantics."""
import json

import pytest
from amphora_contracts_research import (
    CategoricalMeasurement,
    CensoredMeasurement,
    MeasurementQuantity,
    MissingMeasurement,
    NumericMeasurement,
    SeriesMeasurement,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

Q = {"value":"1.2300e-2","unit":"mg/L"}
NUMERIC = {"kind":"numeric","quantity":Q,"uncertainty":None}
MISSING = {"kind":"missing","reason":"not_reported"}


@pytest.mark.parametrize("model,payload",[
    (MeasurementQuantity,Q),(NumericMeasurement,NUMERIC),
    (CensoredMeasurement,{"kind":"censored","lower":None,"upper":{"quantity":Q,"inclusive":False}}),
    (CategoricalMeasurement,{"kind":"categorical","label":"reported-positive"}),(MissingMeasurement,MISSING),
    (SeriesMeasurement,{"kind":"series","x_unit":"s","y_unit":"mg/L","points":[{"x":{"value":"0","unit":"s"},"y":MISSING}]}),
])
def test_variants_keep_original_json(model,payload):
    result = model.model_validate_json(json.dumps(payload))
    assert json.loads(result.model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("value",[1,1.2,True,None,"NaN","Infinity","01","+1","1.","1,2","1\n","1\r\n","1"*129])
def test_numbers_require_bounded_exact_decimal_text(value):
    payload = {"value":value,"unit":"g"}
    with pytest.raises(ValidationError):
        MeasurementQuantity.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(MeasurementQuantity.model_json_schema()).iter_errors(payload))


@pytest.mark.parametrize("unit",["","g/L\n","mg / L",None,1,"u"*33])
def test_units_are_explicit_bounded_tokens(unit):
    payload = {"value":"1","unit":unit}
    with pytest.raises(ValidationError):
        MeasurementQuantity.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(MeasurementQuantity.model_json_schema()).iter_errors(payload))


def test_numeric_boolean_limit_inclusion_cannot_coerce():
    payload = {"kind":"censored","lower":None,"upper":{"quantity":Q,"inclusive":1}}
    with pytest.raises(ValidationError):
        CensoredMeasurement.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(CensoredMeasurement.model_json_schema()).iter_errors(payload))


def test_nested_values_cannot_smuggle_an_acceptance_flag():
    payload = {**NUMERIC,"scientifically_established":True}
    with pytest.raises(ValidationError):
        NumericMeasurement.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(NumericMeasurement.model_json_schema()).iter_errors(payload))
