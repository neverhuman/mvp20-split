import json

import pytest
from amphora_solver_mutate.kernel import compute

from .test_contract import golden


def test_rejected_middle_proposal_does_not_leave_a_scoring_seed_gap():
    value = golden()["input"]
    value["state"]["config"]["reject_mutation_seeds"] = [10018]
    result = json.loads(compute(json.dumps(value)))
    candidates = [item["candidate"] for item in result["candidates"]]
    assert [item["candidate_id"] for item in candidates] == ["g1p0", "g1p2"]
    assert [item["proposal_seed"] for item in candidates] == [10017, 10019]
    assert [item["scoring_seed"] for item in candidates] == [10017, 10018]
    assert [item["parent_ids"] for item in candidates] == [["c0"], ["c2"]]


def test_parent_outside_current_population_is_rejected():
    value = golden()["input"]
    value["parents"][0]["candidate_id"] = "foreign-parent"
    with pytest.raises(ValueError, match="parent_not_current"):
        compute(json.dumps(value))
