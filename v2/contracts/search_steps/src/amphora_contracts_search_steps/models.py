"""Graph-step transport, separate from domain-neutral numeric search records."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Scope, WireModel
from amphora_contracts_graph_runtime import MissingValue
from amphora_contracts_search import (
    EvaluationObservation,
    EvaluationRequest,
    SearchCheckpoint,
    SearchSpec,
)
from pydantic import Field


class SearchStepContext(WireModel):
    original_specification: SearchSpec
    checkpoint: SearchCheckpoint
    checkpoint_artifact: ArtifactRef


class EvaluationRequestBatch(WireModel):
    schema_version: Literal["1"]
    scope: Scope
    specification_sha256: Digest
    checkpoint_artifact: ArtifactRef
    requests: Annotated[tuple[EvaluationRequest, ...], Field(max_length=128)]


class CollectedEvaluations(SearchStepContext):
    results: Annotated[tuple[EvaluationObservation | MissingValue, ...], Field(max_length=128)]
