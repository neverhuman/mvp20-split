"""Wire input reconstructs exact specimen/state/context constraints."""
from dataclasses import replace

import pytest
from amphora_contracts_research import ExperimentDefinition
from amphora_research.experiments import wire
from amphora_research.experiments.identity import ExperimentError, ExperimentIdentity

from .fixtures import experiment


@pytest.mark.parametrize("known",[True,False])
def test_unknown_and_known_state_remain_distinct_through_json(known):
    original = experiment(known)
    successor = replace(original,identity=ExperimentIdentity(replace(original.identity.reference,revision=2),original.identity.reference))
    for value in (original,successor):
        assert wire.from_wire(ExperimentDefinition.model_validate_json(wire.to_wire(value).model_dump_json())) == value


def test_shape_valid_sample_swap_is_not_accepted_by_domain():
    value = wire.to_wire(experiment())
    wrong = value.expectations[0].model_copy(update={"sample":value.expectations[0].sample.model_copy(update={"sample_id":"swapped"})})
    with pytest.raises(ExperimentError,match="expectation_sample_unbound"):
        wire.from_wire(value.model_copy(update={"expectations":(wrong,)}))
