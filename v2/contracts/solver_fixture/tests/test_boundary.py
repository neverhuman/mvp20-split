"""Independent invalid-boundary oracles for the explicit synthetic-only payload profile."""

import json

import pytest
from amphora_contracts_solver_fixture import Candidate, ModuleEnvelope, SolverConfig
from pydantic import ValidationError


def config(**changes):
    return {"source_pins": {key: "a" * 64 for key in ("cli", "engine", "ranking")},
            "seed": 17, "population": 3, "generations": 2, **changes}


@pytest.mark.parametrize("change", [
    {"population": 0}, {"population": 9}, {"generations": 9}, {"seed": True}, {"seed": "17"},
    {"molecule": "undeclared"}, {"source_pins": {"cli": "wrong", "engine": "b" * 64, "ranking": "c" * 64}},
])
def test_invalid_fixture_configuration_is_not_coerced(change):
    with pytest.raises(ValidationError):
        SolverConfig.model_validate_json(json.dumps(config(**change)))


def test_seed_and_generation_zero_remain_distinct_from_absence():
    value = SolverConfig.model_validate_json(json.dumps(config(seed=0, generations=0)))
    assert value.seed == value.generations == 0 and value.population == 3


def test_fixture_envelope_cannot_claim_scientific_authority():
    with pytest.raises(ValidationError):
        ModuleEnvelope.model_validate_json('{"module_id":"solvency","status":"SYNTHETIC","authority":"VALIDATED"}')


def test_candidate_cannot_smuggle_a_changed_molecular_representation():
    raw = {"candidate_id": "c0", "parent_ids": [], "generation": 0, "proposal_index": 0,
           "proposal_seed": 17, "scoring_seed": 17, "structure": "generated-molecule"}
    with pytest.raises(ValidationError):
        Candidate.model_validate_json(json.dumps(raw))
