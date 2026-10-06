"""Interchange and unknown-value oracles, independently of future operators."""

import copy
import json
from pathlib import Path

import amphora_contracts_candidate_spaces as wire
import jsonschema
import pytest
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[2] / "examples"
MODELS = {
    "numeric-design": wire.NumericDesign,
    "polymer-design": wire.PolymerDesign,
    "sequence-design": wire.SequenceDesign,
    "numeric-request": wire.NumericMoveRequest,
    "polymer-request": wire.PolymerMoveRequest,
    "sequence-request": wire.SequenceMoveRequest,
    "change": wire.ProposedDesignChange,
}


def example(name):
    return json.loads((EXAMPLES / (name + ".json")).read_bytes())


@pytest.mark.parametrize("name", MODELS)
def test_example_roundtrip_and_schema(name):
    model, data = MODELS[name], example(name)
    parsed = model.model_validate_json(json.dumps(data))
    assert parsed.model_dump(mode="json") == data
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(data, schema)


def test_unknown_polymer_fields_are_required_null_not_defaults():
    data = example("polymer-design")
    assert all(value is None for value in data["metadata"].values())
    parsed = wire.PolymerDesign.model_validate_json(json.dumps(data))
    assert parsed.composition is None and parsed.metadata.tacticity is None
    for field in data["metadata"]:
        missing = copy.deepcopy(data)
        del missing["metadata"][field]
        with pytest.raises(ValidationError):
            wire.PolymerDesign.model_validate_json(json.dumps(missing))
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(missing, wire.PolymerDesign.model_json_schema())


@pytest.mark.parametrize("name,field,value", [
    ("numeric-design", "authority", "scientific"),
    ("numeric-design", "coordinates", []),
    ("polymer-design", "kind", "sequence"),
    ("polymer-design", "repeat_units", []),
    ("sequence-design", "alphabet", "protein"),
    ("sequence-design", "sequence", ""),
    ("sequence-design", "sequence", "ACGX"),
    ("sequence-design", "sequence", "acgt"),
    ("sequence-design", "sequence", "ACGT\n"),
    ("sequence-design", "sequence", "A" * 4097),
    ("sequence-design", "tacticity", "atactic"),
    ("sequence-request", "move", {"kind": "replace_unit", "site_id": "s0", "unit_id": "A"}),
    ("polymer-request", "move", {"kind": "substitute_base", "position": 0, "base": "A"}),
], ids=["authority", "no-coordinates", "wrong-kind", "no-units", "wrong-alphabet", "empty-sequence",
        "illegal-symbol", "lowercase", "trailing-newline", "capacity", "foreign-field",
        "polymer-move-on-sequence", "sequence-move-on-polymer"])
def test_closed_invalid_shapes_reject_in_both_consumers(name, field, value):
    model, data = MODELS[name], example(name)
    data[field] = value
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, model.model_json_schema())


def test_explicit_polymer_descriptors_are_preserved():
    data = example("polymer-design")
    data["metadata"].update(tacticity="isotactic", sequence_arrangement="defined",
        degree_of_polymerization=100, distribution={"number_average_dp": 100.0,
        "weight_average_dp": 120.0, "dispersity": 1.2}, branching="linear",
        end_groups=[{"site_id": "s0", "label": "toy-end"}], bigsmiles="synthetic-placeholder")
    parsed = wire.PolymerDesign.model_validate_json(json.dumps(data))
    assert parsed.model_dump(mode="json") == data
    jsonschema.validate(data, wire.PolymerDesign.model_json_schema())


def test_semantic_legality_remains_domain_owned():
    # Transport can carry a bad proposal; a tool must reconstruct and reject it.
    data = example("numeric-design")
    data["coordinates"][0].update(lower=2.0, upper=-2.0)
    assert wire.NumericDesign.model_validate_json(json.dumps(data))
    jsonschema.validate(data, wire.NumericDesign.model_json_schema())
