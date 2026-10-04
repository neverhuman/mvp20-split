"""Focused read-only routes use existing scientific JSON/authentication limits."""

from amphora_contracts_research import ExperimentRevisionRef
from amphora_contracts_research_views import (
    ObservationSeriesRequest,
    PropertyViewRequest,
    SpecimenViewRequest,
)


def attach(register, operations):
    for name, model, operation in (
        ("catalog", ExperimentRevisionRef, operations.catalog),
        ("specimens", SpecimenViewRequest, operations.specimens),
        ("properties", PropertyViewRequest, operations.properties),
        ("observation-series", ObservationSeriesRequest, operations.series),
    ):
        register("/v1/research-explore/" + name, model, operation)
