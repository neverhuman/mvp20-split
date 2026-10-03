"""Original result and quality claims remain separate from match/acceptance decisions."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SafePositiveInt, SchemaRef, Scope, WireModel
from pydantic import Field

from .experiments import ControlRole, ExperimentRevisionRef
from .identity import MaterialStateRevisionRef, SampleRevisionRef
from .measurements import MeasurementValue


class ObservationRevisionRef(WireModel):
    scope: Scope
    observation_id: Identifier
    revision: SafePositiveInt


class ObservationTarget(WireModel):
    experiment: ExperimentRevisionRef | None
    expectation_id: Identifier | None
    replicate_id: Identifier | None


class ObservationSpecimen(WireModel):
    sample: SampleRevisionRef | None
    material_state: MaterialStateRevisionRef | None


class ObservationMethod(WireModel):
    method: SchemaRef | None
    context: ArtifactRef | None


class ObservationBindingRecord(WireModel):
    target: ObservationTarget
    specimen: ObservationSpecimen
    measurement: ObservationMethod
    role: ControlRole | None


class ObservationQuality(WireModel):
    controls: Literal["passed","failed","unknown"]
    flags: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class ObservationRevision(WireModel):
    wire_version: Literal["1"]
    reference: ObservationRevisionRef
    supersedes: ObservationRevisionRef | None
    source: ArtifactRef
    binding: ObservationBindingRecord
    value: MeasurementValue
    quality: ObservationQuality
