import json

import pytest
from amphora_contracts_population_steps import PopulationSliceRequest, SeedPopulationRequest, population_step_schema


def source():
    return {"artifact_id": "preparation", "scope": {"tenant_id": "test", "project_id": "population"},
            "sha256": "a" * 64, "media_type": "application/json", "schema_ref": {
                "schema_id": "population-step.prepared", "version": "1", "sha256": "b" * 64}, "size_bytes": 100}


@pytest.mark.parametrize("limit", [0, 33, True, "32", 1.5])
def test_slice_limit_does_not_relax_population_or_legacy_bounds(limit):
    with pytest.raises(ValueError):
        PopulationSliceRequest.model_validate_json(json.dumps({"schema_version": "1", "prepared": source(), "start_index": 0, "limit": limit}))


def test_seed_uses_reference_and_slice_strict_closed_shape():
    seed = SeedPopulationRequest.model_validate_json(json.dumps({"schema_version": "1", "specification": source()}))
    assert seed.specification.artifact_id == "preparation"
    for index in (0, 1000):
        result = PopulationSliceRequest.model_validate_json(json.dumps({"schema_version": "1", "prepared": source(), "start_index": index, "limit": 32}))
        assert result.start_index == index
    with pytest.raises(ValueError):
        PopulationSliceRequest.model_validate_json(json.dumps({"schema_version": "1", "prepared": source(), "start_index": 1001, "limit": 32}))
    with pytest.raises(ValueError):
        SeedPopulationRequest.model_validate_json(json.dumps({"schema_version": "1", "specification": source(), "run_id": "caller-invented"}))
    assert population_step_schema("population-step.seed").schema_id == "population-step.seed"
