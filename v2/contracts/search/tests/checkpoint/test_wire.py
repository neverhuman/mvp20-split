import json
from pathlib import Path

import pytest
from amphora_contracts_search import (
    EvaluationObservation,
    EvaluationRequest,
    SearchCheckpoint,
    SearchSpec,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name,model", [("specification", SearchSpec), ("checkpoint", SearchCheckpoint),
                                      ("request", EvaluationRequest), ("observation", EvaluationObservation)])
def test_language_neutral_roundtrip_and_frozen_records(name, model):
    raw = (FIXTURES / (name + ".json")).read_bytes()
    record = model.model_validate_json(raw)
    assert model.model_validate_json(record.model_dump_json()) == record
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(json.loads(raw))
    with pytest.raises(ValidationError):
        record.schema_version = "2"


@pytest.mark.parametrize("case", ["version", "rng", "seed", "counter", "phase", "owner_acceptance", "pickle", "draw_counter_bool",
                                 "objective_direction", "population_bound", "generation_budget", "infinite_gene", "empty_vector"])
def test_closed_wire_boundary_rejects_invalid_shapes(case):
    value = json.loads((FIXTURES / "checkpoint.json").read_bytes())
    if case == "version": value["schema_version"] = "2"
    if case == "rng": value["rng"]["algorithm"] = "python-pickle"
    if case == "seed": value["rng"]["seed"] = "seed"
    if case == "counter": value["rng"]["counter"] = 9007199254740992
    if case == "phase": value["phase"] = "accepted_science"
    if case == "owner_acceptance": value["accepted"] = True
    if case == "pickle": value["rng"]["payload"] = "opaque-object"
    if case == "draw_counter_bool": value["attempts"][0]["draws"]["start"] = True
    if case == "objective_direction": value["specification"]["objectives"][0]["direction"] = "best"
    if case == "population_bound": value["specification"]["budget"]["population_size"] = 129
    if case == "generation_budget": value["specification"]["budget"]["max_generations"] = -1
    if case == "infinite_gene": value["attempts"][0]["genes"] = [float("inf")]
    if case == "empty_vector": value["attempts"][0]["genes"] = []
    with pytest.raises(ValidationError):
        SearchCheckpoint.model_validate_json(json.dumps(value))


def test_unknown_fitness_cannot_carry_substitute_scores():
    value = json.loads((FIXTURES / "observation.json").read_bytes())
    value["outcome"] = {"status": "unknown", "reason_code": "missing_evidence", "evidence": []}
    record = EvaluationObservation.model_validate_json(json.dumps(value))
    assert record.outcome.status == "unknown"
    value["outcome"]["objectives"] = [{"objective_id": "cost", "unit": "dimensionless", "value": 0.0}]
    with pytest.raises(ValidationError):
        EvaluationObservation.model_validate_json(json.dumps(value))


def test_finite_observation_and_closed_provenance_labels():
    value = json.loads((FIXTURES / "observation.json").read_bytes())
    value["outcome"]["quality"] = "scientifically_proven"
    with pytest.raises(ValidationError):
        EvaluationObservation.model_validate_json(json.dumps(value))
    value["outcome"]["quality"] = "synthetic"
    value["outcome"]["objectives"][0]["value"] = float("nan")
    with pytest.raises(ValidationError):
        EvaluationObservation.model_validate_json(json.dumps(value))
