"""A retained generation is a precise cut, not an arbitrary reusable DTO."""

import copy
import json

import pytest
from amphora_solver_retain.kernel import compute

from .test_contract import golden


def next_generation():
    value = golden()["input"]
    value["batch"]["state"]["config"]["generations"] = 2
    state = json.loads(compute(json.dumps(value)))
    value["batch"]["state"] = state
    value["batch"]["generation"] = 1
    for index, (request, result) in enumerate(zip(value["batch"]["candidates"], value["results"], strict=True)):
        candidate = {**request["candidate"], "candidate_id": f"g1p{index}", "generation": 1,
            "parent_ids": [f"c{index}"], "proposal_seed": 10017 + index, "scoring_seed": 10017 + index}
        request["candidate"] = candidate
        result["candidate"] = copy.deepcopy(candidate)
    return value


@pytest.mark.parametrize("case,reason", [
    ("generation", "generation_cut_mismatch"), ("old_duplicate", "duplicate_candidate_identity"),
    ("new_duplicate", "duplicate_candidate_identity"), ("collision", "duplicate_candidate_identity"),
    ("missing_checkpoint", "checkpoint_cut_mismatch"), ("changed_checkpoint", "checkpoint_cut_mismatch"),
    ("changed_current", "current_not_in_cumulative"), ("missing_slot", "result_membership_mismatch"),
    ("module_order", "module_order_mismatch"), ("proposal_hash", "solver_source_hash_changed"),
])
def test_invalid_retained_cut_cannot_produce_successor_checkpoint(case, reason):
    value = next_generation()
    # The unmodified request is a valid generation-1 continuation.
    assert json.loads(compute(json.dumps(value)))["generation"] == 1
    batch = value["batch"]
    state = batch["state"]
    if case == "generation":
        batch["generation"] = 2
    elif case == "old_duplicate":
        state["cumulative"].append(copy.deepcopy(state["cumulative"][0]))
    elif case == "new_duplicate":
        batch["candidates"][1] = copy.deepcopy(batch["candidates"][0])
    elif case == "collision":
        batch["candidates"][0]["candidate"]["candidate_id"] = "c0"
    elif case == "missing_checkpoint":
        state["checkpoints"] = []
    elif case == "changed_checkpoint":
        state["checkpoints"][0]["cumulative_ids"] = ["unrecorded"]
    elif case == "changed_current":
        state["current"][0]["candidate"]["candidate_id"] = "unrecorded"
        state["checkpoints"][0]["current_ids"][0] = "unrecorded"
    elif case == "missing_slot":
        value["results"].pop()
    elif case == "module_order":
        value["results"][0]["modules"].reverse()
    else:
        batch["candidates"][0]["source_pins"]["engine"] = "f" * 64
    with pytest.raises(ValueError, match=reason):
        compute(json.dumps(value))


def test_nonempty_initial_state_is_not_a_valid_retained_checkpoint():
    value = golden()["input"]
    old = copy.deepcopy(value["results"][0])
    old["candidate"]["candidate_id"] = "uncheckpointed"
    value["batch"]["state"].update(current=[old], cumulative=[copy.deepcopy(old)])
    with pytest.raises(ValueError, match="nonempty_initial_state"):
        compute(json.dumps(value))
