"""Language-neutral fixture validation plus strict input/serialization compatibility."""

import copy
import json

import pytest
from export_schemas import MODELS, ROOT
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((ROOT / "contracts/fixtures/v1/wire_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", [c for c in CASES if c["model"].startswith("tools.")], ids=lambda case: case["name"])
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


def test_unknown_fields_and_versions_not_silently_dropped():
    case = copy.deepcopy(next(c for c in CASES if c["name"] == "valid-invocation"))
    case["payload"]["schema_version"] = "2"
    case["payload"]["override_authority"] = True
    with pytest.raises(ValidationError) as error:
        MODELS[case["model"]].model_validate_json(json.dumps(case["payload"]))
    assert {e["type"] for e in error.value.errors()} == {"literal_error", "extra_forbidden"}
