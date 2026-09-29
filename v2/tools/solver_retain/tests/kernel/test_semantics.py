import json

import pytest
from amphora_solver_retain.kernel import compute

from .test_contract import golden


def missing(index):
    return {"kind": "missing", "member_id": str(index), "reason_code": "tool_failed"}


def test_partial_failure_preserves_request_association_without_compacting_before_match():
    value = golden()["input"]
    value["results"][1] = missing(1)
    result = json.loads(compute(json.dumps(value)))
    assert [item["candidate"]["candidate_id"] for item in result["current"]] == ["c0", "c2"]
    assert result["checkpoints"][0]["failed_ids"] == ["c1"]


def test_reversed_result_slots_cannot_silently_score_the_wrong_parent():
    value = golden()["input"]
    value["results"].reverse()
    with pytest.raises(ValueError, match="result_candidate_mismatch"):
        compute(json.dumps(value))


def test_all_failed_does_not_publish_an_empty_parent_checkpoint():
    value = golden()["input"]
    value["results"] = [missing(index) for index in range(3)]
    with pytest.raises(ValueError, match="no_successful_candidates"):
        compute(json.dumps(value))
