import json

import pytest
from amphora_numeric_affine.kernel import compute
from pydantic import ValidationError


@pytest.mark.parametrize("parameters,expected", [
    ({"values": [-1, 0, 1], "a": -2, "b": 3}, [5, 3, 1]),
    ({"values": [-10, 0, 20], "a": 0, "b": -1}, [-1, -1, -1]),
    ({"values": [0.5, 2], "a": 2, "b": 0.25}, [1.25, 4.25]),
    ({"values": [], "a": 1, "b": 0}, []),
])
def test_independent_golden_results(parameters, expected):
    raw = json.dumps(parameters).encode()
    assert json.loads(compute(raw)) == {"schema_version": "1", "values": expected}
    assert compute(raw) == compute(raw)


@pytest.mark.parametrize("change", [
    {"a": True}, {"a": "2"}, {"a": 1e101}, {"b": float("nan")}, {"values": [float("inf")]},
    {"values": [0] * 1025}, {"extra": 1}, {"schema_version": "2"},
])
def test_invalid_input_never_produces_success(change):
    with pytest.raises(ValidationError):
        compute(json.dumps({"values": [1], "a": 1, "b": 0, **change}).encode())
