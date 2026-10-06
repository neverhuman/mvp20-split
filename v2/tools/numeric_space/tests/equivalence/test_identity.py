import hashlib
import json
from pathlib import Path

from amphora_contracts_candidate_spaces import NumericDesign
from amphora_numeric_space import EQUIVALENCE, PROFILE, NumericCanonical


def data():
    record = json.loads(
        (Path(__file__).parents[1] / "legality/request.json").read_bytes()
    )["source"]
    record["profile"] = PROFILE.model_dump(mode="json")
    record["coordinates"].append(
        {"coordinate_id": "y", "unit": "1", "lower": -3.0, "upper": 3.0, "value": 2.0}
    )
    return record


def identity(record):
    return NumericCanonical(NumericDesign.model_validate_json(json.dumps(record)))


def test_ordered_coordinate_bytes_and_profile_are_explicit():
    source = data()
    result = identity(source)
    expected = json.dumps(
        source, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert (
        result.bytes == expected
        and result.sha256 == hashlib.sha256(expected).hexdigest()
    )
    assert result.policy == EQUIVALENCE and result.policy != PROFILE
    source["coordinates"].reverse()
    assert identity(source).sha256 != result.sha256


def test_unit_bound_and_scope_changes_cannot_share_identity():
    expected = identity(data()).sha256
    for change in ("unit", "bound", "scope"):
        source = data()
        if change == "unit":
            source["coordinates"][0]["unit"] = "kg"
        elif change == "bound":
            source["coordinates"][0]["upper"] = 3.0
        else:
            source["scope"]["project_id"] = "other"
        assert identity(source).sha256 != expected
