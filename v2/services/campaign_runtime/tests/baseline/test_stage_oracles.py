"""Pure stage composition against authored oracles; not yet graph/process acceptance."""

import json

import pytest
from amphora_solver_mutate.kernel import compute as mutate
from amphora_solver_retain.kernel import compute as retain
from amphora_solver_score.kernel import compute as score
from amphora_solver_seed.kernel import compute as seed
from amphora_solver_select.kernel import compute as select

from .test_v1_baseline import FIXTURES

ORACLES = json.loads((FIXTURES / "expected_traces.json").read_bytes())["cases"]
PINS = {key: value["sha256"] for key, value in json.loads((FIXTURES / "behavior_graph.json").read_bytes())["sources"].items()}


def call(stage, value):
    return json.loads(stage(json.dumps(value)))


@pytest.mark.parametrize("case", ORACLES, ids=[case["name"] for case in ORACLES])
def test_stage_trace_matches_independent_source_oracle(case):
    batch = call(seed, {**case["config"], "source_pins": PINS})
    state = None
    for expected in case["generations"]:
        if expected["generation"]:
            selection = call(select, state)
            assert [parent["candidate_id"] for parent in selection["parents"]] == expected["selected_parents"]
            assert selection["used_fallback"] is expected["parent_fallback"]
            batch = call(mutate, selection)
        candidates = [item["candidate"] for item in batch["candidates"]]
        for field in ("candidate_id", "proposal_seed", "scoring_seed"):
            assert [item[field] for item in candidates] == expected[field + "s"]
        if "parent_ids" in expected:
            assert [item["parent_ids"][0] for item in candidates] == expected["parent_ids"]
        assert [item["proposal_seed"] for item in batch["rejections"]] == expected.get("rejected_proposal_seeds", [])
        slots = [None] * len(candidates)
        failed = []
        # Test controller completes in reverse order; slots must remain associated with requests.
        for index in reversed(range(len(candidates))):
            try:
                slots[index] = call(score, batch["candidates"][index])
            except ValueError as error:
                assert str(error) == "synthetic_scoring_failure"
                slots[index] = {"kind": "missing", "member_id": str(index), "reason_code": "tool_failed"}
                failed.append(candidates[index]["candidate_id"])
        assert list(reversed(failed)) == expected.get("failed_ids", [])
        if not expected["current"]:
            with pytest.raises(ValueError, match="no_successful_candidates"):
                call(retain, {"batch": batch, "results": slots})
            assert case["terminal"] == "blocked" and case["checkpoints"] == []
            return
        state = call(retain, {"batch": batch, "results": slots})
        assert [item["candidate"]["candidate_id"] for item in state["current"]] == expected["current"]
        assert [item["candidate"]["candidate_id"] for item in state["cumulative"]] == expected["cumulative"]
    assert [item["generation"] for item in state["checkpoints"]] == case["checkpoints"]
    assert case["terminal"] == "completed"
