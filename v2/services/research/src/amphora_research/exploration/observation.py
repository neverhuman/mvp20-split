"""Reported measurement and declared context remain separate from scientific matching."""

from amphora_contracts_research import ObservationRevision
from amphora_contracts_research_views import (
    ObservationSeriesPage,
    ObservationSeriesRequest,
    PropertyViewRow,
    SeriesDescriptor,
)

from ..observations.wire import from_wire
from .query import ViewQuery, bounded, canonical, require


class ObservationProjection:
    def __init__(self, record):
        require(type(record) is ObservationRevision, "observation_type")
        record = ObservationRevision.model_validate_json(record.model_dump_json())
        require(len(canonical(record)) <= 1048576, "record_limit")
        from_wire(record)
        self.record = record

    def preview(self):
        value = self.record.value
        return (
            SeriesDescriptor(
                kind="series",
                x_unit=value.x_unit,
                y_unit=value.y_unit,
                point_count=len(value.points),
            )
            if value.kind == "series"
            else value
        )

    def row(self, experiment, expectations):
        target = self.record.binding.target
        expectation = None
        if target.experiment is None or target.expectation_id is None:
            status = "unbound"
        elif target.experiment != experiment:
            status = "different_experiment"
        else:
            expectation = expectations.get(target.expectation_id)
            status = (
                "unknown_expectation" if expectation is None else "declared_expectation"
            )
        record = self.record
        return PropertyViewRow(
            reference=record.reference,
            supersedes=record.supersedes,
            source=record.source,
            binding=record.binding,
            quality=record.quality,
            value=self.preview(),
            context_link=status,
            expectation=expectation,
        )

    def series(self, request):
        require(type(request) is ObservationSeriesRequest, "series_request")
        query = ViewQuery.prepare(request)
        request = query.request
        require(request.observation == self.record.reference, "observation_identity")
        value = self.record.value
        require(value.kind == "series", "not_series")
        start, end = query.window(len(value.points))
        return bounded(
            ObservationSeriesPage(
                wire_version="1",
                request=request,
                query_sha256=query.sha256,
                total=len(value.points),
                x_unit=value.x_unit,
                y_unit=value.y_unit,
                source=self.record.source,
                binding=self.record.binding,
                quality=self.record.quality,
                points=value.points[start:end],
                next_position=query.next_position(end, len(value.points)),
            )
        )
