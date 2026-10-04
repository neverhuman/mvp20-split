"""Owned synthetic experiment/observation fixtures, no peer or scientific claim."""

import pytest
from amphora_research.experiments.wire import to_wire as experiment_wire
from amphora_research.observations.wire import to_wire as observation_wire

from ..experiments.fixtures import experiment
from ..observations.test_matching import observation


@pytest.fixture
def records():
    return experiment_wire(experiment()), observation_wire(observation())


from types import SimpleNamespace

from amphora_contracts_research import (
    MeasurementQuantity,
    MissingMeasurement,
    SeriesMeasurement,
    SeriesMeasurementPoint,
)
from amphora_research.experiments.store import ExperimentStore
from amphora_research.observations.store import ObservationStore

from ..material_state.storage_fixtures import publish_specimen


@pytest.fixture
def prepared(ledger):
    identities, scope = ledger
    state, plan, first = publish_specimen(identities, scope)
    ExperimentStore(identities.engine).publish(scope, "fixture", plan)
    store = ObservationStore(identities.engine)
    store.publish(scope, "fixture", first)
    second = first.model_copy(
        update={
            "reference": first.reference.model_copy(
                update={"observation_id": "series"}
            ),
            "value": SeriesMeasurement(
                kind="series",
                x_unit="s",
                y_unit="mg/L",
                points=(
                    SeriesMeasurementPoint(
                        x=MeasurementQuantity(value="1.00", unit="s"), y=first.value
                    ),
                    SeriesMeasurementPoint(
                        x=MeasurementQuantity(value="1.00", unit="s"),
                        y=MissingMeasurement(kind="missing", reason="not_measured"),
                    ),
                ),
            ),
        }
    )
    store.publish(scope, "fixture", second)
    return SimpleNamespace(
        identities=identities,
        scope=scope,
        engine=identities.engine,
        state=state,
        plan=plan,
        first=first,
        second=second,
        store=store,
    )
