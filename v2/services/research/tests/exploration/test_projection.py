"""Preserve original scientific context and measurement meaning under bounded paging."""

import pytest
from amphora_contracts_research import (
    CategoricalMeasurement,
    CensorBound,
    CensoredMeasurement,
    MeasurementInterval,
    MeasurementQuantity,
    MissingMeasurement,
    NumericMeasurement,
    SeriesMeasurement,
    SeriesMeasurementPoint,
)
from amphora_contracts_research_views import (
    ObservationSeriesRequest,
    PropertyViewRequest,
    ResearchViewPosition,
    SpecimenViewRequest,
)
from amphora_research.exploration.experiment import ExperimentProjection
from amphora_research.exploration.observation import ObservationProjection
from amphora_research.exploration.query import ResearchViewError, ViewQuery


def quantity(value, unit="mg/L"):
    return MeasurementQuantity(value=value, unit=unit)


@pytest.mark.parametrize(
    "value",
    [
        NumericMeasurement(
            kind="numeric",
            quantity=quantity("1.2300e-2"),
            uncertainty=MeasurementInterval(
                lower=quantity("0.001"),
                upper=quantity("0.02"),
                description="reported interval",
            ),
        ),
        CensoredMeasurement(
            kind="censored",
            lower=None,
            upper=CensorBound(quantity=quantity("0.100"), inclusive=False),
        ),
        CategoricalMeasurement(kind="categorical", label="inconclusive"),
        MissingMeasurement(kind="missing", reason="not_measured"),
    ],
)
def test_scalar_values_quality_and_binding_are_preserved_without_acceptance(
    records, value
):
    experiment, observation = records
    observation = observation.model_copy(
        update={
            "value": value,
            "quality": observation.quality.model_copy(
                update={"controls": "failed", "flags": ("questionable",)}
            ),
        }
    )
    request = PropertyViewRequest(
        wire_version="1",
        experiment=experiment.reference,
        observations=(observation.reference,),
    )
    page = ExperimentProjection(experiment).properties(request, (observation,))
    row = page.rows[0]
    assert row.value == value and row.binding == observation.binding
    assert row.quality.controls == "failed" and row.quality.flags == ("questionable",)
    assert page.authority == "reported_evidence_only"
    assert page.selection_scope == "explicit_observation_revisions"
    assert (
        row.context_link == "declared_expectation"
        and row.expectation == experiment.expectations[0]
    )
    assert page.protocol == experiment.protocol


@pytest.mark.parametrize(
    "target_changes,status",
    [
        ({"experiment": None}, "unbound"),
        ({"expectation_id": None}, "unbound"),
        ({"expectation_id": "missing"}, "unknown_expectation"),
        ({"experiment_id": "different"}, "different_experiment"),
    ],
)
def test_declared_context_mismatch_remains_visible(records, target_changes, status):
    experiment, observation = records
    changes = dict(target_changes)
    if "experiment_id" in changes:
        changes = {"experiment": experiment.reference.model_copy(update=changes)}
    target = observation.binding.target.model_copy(update=changes)
    modified = observation.model_copy(
        update={"binding": observation.binding.model_copy(update={"target": target})}
    )
    request = PropertyViewRequest(
        wire_version="1",
        experiment=experiment.reference,
        observations=(modified.reference,),
    )
    row = ExperimentProjection(experiment).properties(request, (modified,)).rows[0]
    assert row.context_link == status and row.expectation is None
    assert row.binding.target == target


def test_distinct_preparations_same_candidate_and_unknown_state_are_not_merged(records):
    experiment, _ = records
    first = experiment.samples[0]
    second_state = first.state.model_copy(
        update={
            "reference": first.state.reference.model_copy(
                update={"material_state_id": "prepared-differently"}
            )
        }
    )
    second = first.model_copy(
        update={
            "sample": first.sample.model_copy(
                update={
                    "reference": first.sample.reference.model_copy(
                        update={"sample_id": "second-vial"}
                    ),
                    "material_state": second_state.reference,
                }
            ),
            "state": second_state,
        }
    )
    unknown = first.model_copy(
        update={
            "sample": first.sample.model_copy(
                update={
                    "reference": first.sample.reference.model_copy(
                        update={"sample_id": "unknown-vial"}
                    ),
                    "material_state": None,
                }
            ),
            "state": None,
        }
    )
    expanded = experiment.model_copy(update={"samples": (first, second, unknown)})
    view = ExperimentProjection(expanded)
    request = SpecimenViewRequest(
        wire_version="1", experiment=expanded.reference, limit=1
    )
    pages = []
    while True:
        page = view.specimens(request)
        pages.append(page)
        if page.next_position is None:
            break
        request = request.model_copy(update={"position": page.next_position})
    rows = [p.rows[0] for p in pages]
    assert len(rows) == 3 and all(p.total == 3 for p in pages)
    assert rows[0].sample.candidate == rows[1].sample.candidate
    assert rows[0].material.reference != rows[1].material.reference
    assert rows[2].material is None and rows[2].sample.material_state is None


def test_series_windows_preserve_duplicate_unsorted_x_and_missing_censored_ordinates(
    records,
):
    _, record = records
    points = (
        SeriesMeasurementPoint(x=quantity("2.00", "s"), y=record.value),
        SeriesMeasurementPoint(
            x=quantity("2.00", "s"),
            y=MissingMeasurement(kind="missing", reason="failed_read"),
        ),
        SeriesMeasurementPoint(
            x=quantity("1.00", "s"),
            y=CensoredMeasurement(
                kind="censored",
                lower=CensorBound(quantity=quantity("0.1"), inclusive=True),
                upper=None,
            ),
        ),
    )
    record = record.model_copy(
        update={
            "value": SeriesMeasurement(
                kind="series", x_unit="s", y_unit="mg/L", points=points
            )
        }
    )
    view = ObservationProjection(record)
    assert view.preview().point_count == 3
    request = ObservationSeriesRequest(
        wire_version="1", observation=record.reference, limit=2
    )
    first = view.series(request)
    second = view.series(request.model_copy(update={"position": first.next_position}))
    assert first.points + second.points == points and second.next_position is None
    assert first.binding == record.binding and first.source == record.source
    assert first.query_sha256 == second.query_sha256
    with pytest.raises(ResearchViewError, match="position_query"):
        view.series(
            request.model_copy(update={"limit": 1, "position": first.next_position})
        )


def test_property_selection_pins_order_revision_and_complete_query(records):
    experiment, first = records
    second = first.model_copy(
        update={
            "reference": first.reference.model_copy(update={"observation_id": "second"})
        }
    )
    request = PropertyViewRequest(
        wire_version="1",
        experiment=experiment.reference,
        observations=(second.reference, first.reference),
        limit=1,
    )
    view = ExperimentProjection(experiment)
    page = view.properties(request, (second,))
    continued = request.model_copy(update={"position": page.next_position})
    last = view.properties(continued, (first,))
    assert (
        page.rows[0].reference == second.reference
        and last.rows[0].reference == first.reference
    )
    assert last.next_position is None
    with pytest.raises(ResearchViewError, match="page_identity"):
        view.properties(request, (first,))
    with pytest.raises(ResearchViewError, match="position_query"):
        view.properties(
            continued.model_copy(
                update={"observations": tuple(reversed(request.observations))}
            ),
            (second,),
        )
    with pytest.raises(ResearchViewError, match="duplicate_observation"):
        ViewQuery.prepare(
            request.model_copy(
                update={"observations": (first.reference, first.reference)}
            )
        )
    other = first.reference.model_copy(
        update={
            "scope": first.reference.scope.model_copy(update={"project_id": "other"})
        }
    )
    with pytest.raises(ResearchViewError, match="selection_scope"):
        ViewQuery.prepare(request.model_copy(update={"observations": (other,)}))


def test_query_limits_exact_types_and_record_identity(records):
    experiment, observation = records
    view = ExperimentProjection(experiment)
    request = SpecimenViewRequest(wire_version="1", experiment=experiment.reference)
    catalog = view.catalog()
    assert catalog.experiment == experiment.reference and catalog.limits.rows == 16
    position = ResearchViewPosition(
        query_sha256=ViewQuery.prepare(request).sha256, offset=2
    )
    with pytest.raises(ResearchViewError, match="position_bound"):
        view.specimens(request.model_copy(update={"position": position}))
    with pytest.raises(ResearchViewError, match="experiment_identity"):
        view.specimens(
            request.model_copy(
                update={
                    "experiment": experiment.reference.model_copy(
                        update={"revision": 2}
                    )
                }
            )
        )
    with pytest.raises(ResearchViewError, match="not_series"):
        ObservationProjection(observation).series(
            ObservationSeriesRequest(
                wire_version="1", observation=observation.reference
            )
        )
    with pytest.raises(ResearchViewError, match="observation_identity"):
        ObservationProjection(observation).series(
            ObservationSeriesRequest(
                wire_version="1",
                observation=observation.reference.model_copy(update={"revision": 2}),
            )
        )
    for action in (
        lambda: ExperimentProjection(observation),
        lambda: ObservationProjection(experiment),
        lambda: ViewQuery.prepare(experiment),
        lambda: view.specimens(experiment),
        lambda: ObservationProjection(observation).series(request),
    ):
        with pytest.raises(ResearchViewError):
            action()


def test_wrong_page_cardinality_and_invalid_scientific_measurement_fail(records):
    experiment, observation = records
    request = PropertyViewRequest(
        wire_version="1",
        experiment=experiment.reference,
        observations=(observation.reference,),
    )
    view = ExperimentProjection(experiment)
    for page_records in ((), [observation], (observation, observation)):
        with pytest.raises(ResearchViewError, match="page_records"):
            view.properties(request, page_records)
    malformed = observation.model_copy(
        update={"value": CensoredMeasurement(kind="censored", lower=None, upper=None)}
    )
    with pytest.raises(ValueError, match="censor_limit_required"):
        ObservationProjection(malformed)


def test_series_full_bound_pages_do_not_drop_any_point(records):
    _, record = records
    point = SeriesMeasurementPoint(x=quantity("0", "s"), y=record.value)
    record = record.model_copy(
        update={
            "value": SeriesMeasurement(
                kind="series", x_unit="s", y_unit="mg/L", points=(point,) * 4096
            )
        }
    )
    view = ObservationProjection(record)
    request = ObservationSeriesRequest(wire_version="1", observation=record.reference)
    count = 0
    while True:
        page = view.series(request)
        assert len(page.points) == 256 and page.total == 4096
        assert all(p == point for p in page.points)
        count += len(page.points)
        if page.next_position is None:
            break
        request = request.model_copy(update={"position": page.next_position})
    assert count == 4096
