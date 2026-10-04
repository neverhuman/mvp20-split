"""Immutable experiment/specimen context and explicit selected observation projections."""

from types import MappingProxyType

from amphora_contracts_research import ExperimentDefinition
from amphora_contracts_research_views import (
    MaterialStateSummary,
    PropertyViewPage,
    PropertyViewRequest,
    ResearchViewCapability,
    ResearchViewCatalog,
    ResearchViewLimits,
    SpecimenViewPage,
    SpecimenViewRequest,
    SpecimenViewRow,
    research_view_schema,
)

from ..experiments.wire import from_wire
from .observation import ObservationProjection
from .query import ViewQuery, bounded, canonical, require


class ExperimentProjection:
    def __init__(self, record):
        require(type(record) is ExperimentDefinition, "experiment_type")
        record = ExperimentDefinition.model_validate_json(record.model_dump_json())
        require(len(canonical(record)) <= 1048576, "record_limit")
        from_wire(record)
        self.record = record
        self.expectations = MappingProxyType(
            {e.expectation_id: e for e in record.expectations}
        )

    def catalog(self):
        return bounded(
            ResearchViewCatalog(
                wire_version="1",
                owner="research",
                experiment=self.record.reference,
                views=tuple(
                    ResearchViewCapability(
                        view_id=name,
                        version="1",
                        result_schema=research_view_schema(name),
                    )
                    for name in ("specimens", "properties", "observation_series")
                ),
                limits=ResearchViewLimits(
                    rows=16,
                    selected_observations=128,
                    series_points=256,
                    response_bytes=1048576,
                    source_fetch="separate_data_authority",
                ),
            )
        )

    def _query(self, request, model):
        require(type(request) is model, "experiment_request")
        query = ViewQuery.prepare(request)
        require(
            query.request.experiment == self.record.reference, "experiment_identity"
        )
        return query

    def specimens(self, request):
        query = self._query(request, SpecimenViewRequest)
        start, end = query.window(len(self.record.samples))
        rows = []
        for item in self.record.samples[start:end]:
            state = item.state
            material = (
                None
                if state is None
                else MaterialStateSummary(
                    reference=state.reference,
                    candidate=state.candidate,
                    supersedes=state.supersedes,
                    preparation_count=len(state.preparation),
                    feature_count=len(state.features),
                )
            )
            rows.append(SpecimenViewRow(sample=item.sample, material=material))
        return bounded(
            SpecimenViewPage(
                wire_version="1",
                request=query.request,
                query_sha256=query.sha256,
                total=len(self.record.samples),
                rows=tuple(rows),
                next_position=query.next_position(end, len(self.record.samples)),
            )
        )

    def properties(self, request, records):
        query = self._query(request, PropertyViewRequest)
        request = query.request
        start, end = query.window(len(request.observations))
        require(type(records) is tuple and len(records) == end - start, "page_records")
        rows = tuple(ObservationProjection(record) for record in records)
        require(
            tuple(row.record.reference for row in rows)
            == request.observations[start:end],
            "page_identity",
        )
        return bounded(
            PropertyViewPage(
                wire_version="1",
                request=request,
                query_sha256=query.sha256,
                total=len(request.observations),
                protocol=self.record.protocol,
                authority="reported_evidence_only",
                selection_scope="explicit_observation_revisions",
                rows=tuple(
                    row.row(self.record.reference, self.expectations) for row in rows
                ),
                next_position=query.next_position(end, len(request.observations)),
            )
        )
