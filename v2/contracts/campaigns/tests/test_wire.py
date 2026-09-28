"""Language-neutral fixture validation plus strict input/serialization compatibility."""

import json

import pytest
from export_schemas import MODELS, ROOT
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((ROOT / "contracts/fixtures/v1/wire_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", [c for c in CASES if c["model"].startswith("campaigns.")], ids=lambda case: case["name"])
def test_shared_interchange_fixture(case):
    model = MODELS[case["model"]]
    schema = model.model_json_schema(mode="validation")
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(case["payload"]))
    assert (not errors) == case["valid"]
    raw = json.dumps(case["payload"])
    if case["valid"]:
        obj = model.model_validate_json(raw)
        emitted = json.loads(obj.model_dump_json())
        Draft202012Validator(model.model_json_schema(mode="serialization")).validate(emitted)
        assert model.model_validate_json(obj.model_dump_json()) == obj
    else:
        with pytest.raises(ValidationError):
            model.model_validate_json(raw)
