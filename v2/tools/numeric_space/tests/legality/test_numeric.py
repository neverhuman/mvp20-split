import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_candidate_spaces import NumericDesign, NumericMoveRequest
from amphora_numeric_space import (
    OPERATOR,
    PROFILE,
    NumericDesignError,
    NumericSpace,
    canonical,
)


def payload():
    data = json.loads(Path(__file__).with_name("request.json").read_bytes())
    data["source"]["profile"] = PROFILE.model_dump(mode="json")
    data["operator"] = OPERATOR.model_dump(mode="json")
    return data


def test_move_and_noop_preserve_exact_source_and_pins():
    request = NumericMoveRequest.model_validate_json(json.dumps(payload()))
    space = NumericSpace(request.source)
    result = space.apply(request)
    assert result.result.coordinates[0].value == -1
    assert (
        result.result.scope == request.source.scope and result.result.profile == PROFILE
    )
    assert result.source_sha256 == hashlib.sha256(canonical(request.source)).hexdigest()
    assert request.source.coordinates[0].value == 1
    data = payload()
    data["move"]["value"] = 1.0
    assert (
        space.apply(NumericMoveRequest.model_validate_json(json.dumps(data))).result
        == request.source
    )


@pytest.mark.parametrize(
    "change,code",
    [
        ({"lower": 3.0}, "numeric_coordinate_invalid"),
        ({"value": 3.0}, "numeric_coordinate_invalid"),
        ({"unit": " "}, "numeric_coordinate_invalid"),
    ],
)
def test_invalid_coordinate_rejects(change, code):
    data = payload()["source"]
    data["coordinates"][0].update(change)
    with pytest.raises(NumericDesignError, match=code):
        NumericSpace(NumericDesign.model_validate_json(json.dumps(data)))


def test_duplicate_and_wrong_profile_reject():
    data = payload()["source"]
    data["coordinates"].append(data["coordinates"][0])
    with pytest.raises(NumericDesignError, match="duplicate"):
        NumericSpace(NumericDesign.model_validate_json(json.dumps(data)))
    data = payload()["source"]
    data["profile"]["sha256"] = "f" * 64
    with pytest.raises(NumericDesignError, match="profile"):
        NumericSpace(NumericDesign.model_validate_json(json.dumps(data)))


@pytest.mark.parametrize("which", ["missing", "outside", "operator", "source"])
def test_move_rejection_keeps_original(which):
    data = payload()
    space = NumericSpace(
        NumericMoveRequest.model_validate_json(json.dumps(data)).source
    )
    original = canonical(space.record)
    if which == "missing":
        data["move"]["coordinate_id"] = "unknown"
    elif which == "outside":
        data["move"]["value"] = 4.0
    elif which == "operator":
        data["operator"]["sha256"] = "f" * 64
    else:
        data["source"]["scope"]["project_id"] = "foreign"
    with pytest.raises(NumericDesignError):
        space.apply(NumericMoveRequest.model_validate_json(json.dumps(data)))
    assert canonical(space.record) == original
