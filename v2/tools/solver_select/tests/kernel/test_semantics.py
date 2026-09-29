import copy
import json

import pytest
from amphora_solver_select.kernel import compute

from .test_contract import golden


@pytest.mark.parametrize("old_count,expected,fallback", [(3, ["g1p0", "g1p1"], True), (2, ["g1p0"], False)])
def test_top_n_precedes_intersection_and_only_empty_intersection_falls_back(old_count, expected, fallback):
    value = golden()["input"]
    old = value["cumulative"][:old_count]
    current = copy.deepcopy(value["current"][:2])
    for index, result in enumerate(current):
        result["candidate"].update(candidate_id=f"g1p{index}", generation=1)
    value.update(generation=1, cumulative=old + current, current=current)
    result = json.loads(compute(json.dumps(value)))
    assert [item["candidate_id"] for item in result["parents"]] == expected
    assert result["used_fallback"] is fallback


def test_empty_current_has_a_truthful_failure_instead_of_parent_indexing():
    value = golden()["input"]
    value["current"] = []
    with pytest.raises(ValueError, match="empty_parent_population"):
        compute(json.dumps(value))
