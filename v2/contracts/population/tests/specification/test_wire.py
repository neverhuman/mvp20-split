import copy
import json
from pathlib import Path

import pytest
from amphora_contracts_population import PopulationSpecification
from jsonschema import Draft202012Validator
from pydantic import ValidationError

FIXTURE = Path(__file__).parent / "fixtures/specification.json"


def test_closed_roundtrip_and_both_schema_modes():
    value = json.loads(FIXTURE.read_bytes())
    record = PopulationSpecification.model_validate_json(FIXTURE.read_bytes())
    assert PopulationSpecification.model_validate_json(record.model_dump_json()) == record
    for mode in ("validation", "serialization"):
        schema = record.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)
    with pytest.raises(ValidationError):
        record.profile = "other"


@pytest.mark.parametrize("path,value", [
    (("schema_version",), "2"), (("profile",), "numeric-search-v1"),
    (("revision",), True), (("budget", "population_size"), 1001),
    (("budget", "active_invocations"), 9), (("budget", "dispatch_slice"), 33),
    (("budget", "successor_generations"), 101), (("budget", "max_activations"), 100001),
    (("budget", "deadline_seconds"), 86401), (("selection", "minimum_parents"), 0),
    (("selection", "unavailable"), "substitute_zero"),
    (("selection", "completion"), "first_n"), (("accepted",), True),
    (("variables", 0, "lower"), float("inf")),
])
def test_invalid_wire_rejected_by_model_and_schema(path, value):
    document = json.loads(FIXTURE.read_bytes())
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        PopulationSpecification.model_validate_json(json.dumps(document))
    assert list(Draft202012Validator(PopulationSpecification.model_json_schema()).iter_errors(document))


def test_eight_methods_is_the_closed_bound():
    document = json.loads(FIXTURE.read_bytes())
    first = document["method_graph"]["methods"][0]
    document["method_graph"]["methods"] = [copy.deepcopy(first) for _ in range(9)]
    with pytest.raises(ValidationError):
        PopulationSpecification.model_validate_json(json.dumps(document))
