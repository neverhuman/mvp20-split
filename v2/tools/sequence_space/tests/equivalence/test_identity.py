import hashlib
import json
from pathlib import Path

from amphora_contracts_candidate_spaces import SequenceDesign
from amphora_sequence_space import EQUIVALENCE, PROFILE, SequenceCanonical


def data():
    record = json.loads(
        (Path(__file__).parents[1] / "legality/request.json").read_bytes()
    )["source"]
    record["profile"] = PROFILE.model_dump(mode="json")
    return record


def identity(record):
    return SequenceCanonical(SequenceDesign.model_validate_json(json.dumps(record)))


def test_exact_sequence_bytes_and_policy():
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
    source["sequence"] = "TGCA"
    assert identity(source).sha256 != result.sha256


def test_scope_is_not_implicitly_cross_project_reusable():
    source = data()
    first = identity(source).sha256
    source["scope"]["project_id"] = "other"
    assert identity(source).sha256 != first
