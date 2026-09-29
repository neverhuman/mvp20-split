import json

import pytest
from amphora_solver_score.kernel import compute

from .test_contract import golden


def test_capability_error_keeps_order_and_later_envelopes_without_authority():
    case = golden()
    failing = case["output"]["modules"][0]["module_id"]
    case["input"]["error_modules"] = [failing]
    result = json.loads(compute(json.dumps(case["input"])))
    assert [item["module_id"] for item in result["modules"]] == [item["module_id"] for item in case["output"]["modules"]]
    assert result["modules"][0]["status"] == "ERROR"
    assert all(item["status"] == "SYNTHETIC" for item in result["modules"][1:])
    assert all(item["authority"] == "NO_AUTHORITY" for item in result["modules"])
    assert result["ranked"] is False and result["eligible_objectives"] == 0


def test_candidate_failure_is_distinct_from_capability_error():
    value = golden()["input"]
    value["fail_scoring"] = True
    with pytest.raises(ValueError, match="synthetic_scoring_failure"):
        compute(json.dumps(value))
