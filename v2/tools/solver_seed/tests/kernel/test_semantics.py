import json

from amphora_solver_seed.kernel import compute

from .test_contract import golden


def test_rejection_preserves_proposal_seed_and_compacts_scoring_index():
    value = golden()["input"]
    value["reject_mutation_seeds"] = [18]
    result = json.loads(compute(json.dumps(value)))
    assert [item["candidate"]["candidate_id"] for item in result["candidates"]] == ["c0", "c2"]
    assert [item["candidate"]["proposal_seed"] for item in result["candidates"]] == [17, 19]
    assert [item["candidate"]["scoring_seed"] for item in result["candidates"]] == [17, 18]
    assert [item["proposal_seed"] for item in result["rejections"]] == [18]


def test_original_candidate_is_not_a_mutation_rejection():
    value = golden()["input"]
    value.update(population=1, generations=0, reject_mutation_seeds=[17])
    result = json.loads(compute(json.dumps(value)))
    assert len(result["candidates"]) == 1 and result["rejections"] == []
