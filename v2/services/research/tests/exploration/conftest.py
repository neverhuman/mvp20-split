"""Owned synthetic experiment/observation fixtures, no peer or scientific claim."""

import pytest
from amphora_research.experiments.wire import to_wire as experiment_wire
from amphora_research.observations.wire import to_wire as observation_wire

from ..experiments.fixtures import experiment
from ..observations.test_matching import observation


@pytest.fixture
def records():
    return experiment_wire(experiment()), observation_wire(observation())
