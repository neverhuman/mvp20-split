import json
from pathlib import Path

import pytest
from amphora_contracts_population import CandidateBirth, EvaluationKey, MethodObservation
from jsonschema import Draft202012Validator
from pydantic import ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name,model", [("birth", CandidateBirth), ("key", EvaluationKey), ("observation", MethodObservation)])
def test_wire_roundtrip_and_generated_schemas(name, model):
    raw = (FIXTURES / (name + ".json")).read_bytes()
    record = model.model_validate_json(raw)
    assert model.model_validate_json(record.model_dump_json()) == record
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(json.loads(raw))
    with pytest.raises(ValidationError): record.schema_version = "2"


@pytest.mark.parametrize("name,model,path,value", [
    ("birth", CandidateBirth, ("ordinal",), 1000),
    ("birth", CandidateBirth, ("generation",), True),
    ("birth", CandidateBirth, ("genes",), [float("inf")]),
    ("birth", CandidateBirth, ("parents",), ["a" * 64] * 3),
    ("birth", CandidateBirth, ("schema_version",), "2"),
    ("key", EvaluationKey, ("attempt_id",), "retry-is-not-a-new-key"),
    ("key", EvaluationKey, ("inputs",), []),
    ("key", EvaluationKey, ("generation", "generation"), 101),
    ("observation", MethodObservation, ("outcome", "status"), "pending"),
    ("observation", MethodObservation, ("outcome", "outputs"), []),
    ("observation", MethodObservation, ("outcome", "producer"), None),
    ("observation", MethodObservation, ("accepted_science",), True),
])
def test_closed_shapes(name, model, path, value):
    record = json.loads((FIXTURES / (name + ".json")).read_bytes())
    target = record
    for key in path[:-1]: target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError): model.model_validate_json(json.dumps(record))
