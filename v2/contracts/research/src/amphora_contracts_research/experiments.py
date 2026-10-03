"""Exact method/specimen/expectation transport, with no physical submission authority."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SafePositiveInt, SchemaRef, Scope, WireModel
from pydantic import Field

from .identity import SampleIdentity, SampleRevisionRef
from .materials import MaterialStateRevision
from .measurements import UnitToken

ControlRole = Literal["sample","positive_control","negative_control","blank"]


class ExperimentRevisionRef(WireModel):
    scope: Scope
    experiment_id: Identifier
    revision: SafePositiveInt


class ExperimentSample(WireModel):
    sample: SampleIdentity
    state: MaterialStateRevision | None


class ExperimentProtocol(WireModel):
    method: SchemaRef
    applicability: ArtifactRef
    source: ArtifactRef


class ExperimentReadout(WireModel):
    criterion_id: Identifier
    kind: Literal["numeric","categorical","series"]
    unit: UnitToken | None
    x_unit: UnitToken | None


class ExperimentReplicate(WireModel):
    replicate_id: Identifier
    role: ControlRole


class ExperimentExpectation(WireModel):
    expectation_id: Identifier
    sample: SampleRevisionRef
    readout: ExperimentReadout
    replicate: ExperimentReplicate


class ExperimentDefinition(WireModel):
    wire_version: Literal["1"]
    reference: ExperimentRevisionRef
    supersedes: ExperimentRevisionRef | None
    protocol: ExperimentProtocol
    samples: Annotated[tuple[ExperimentSample, ...],Field(min_length=1,max_length=256)]
    expectations: Annotated[tuple[ExperimentExpectation, ...],Field(min_length=1,max_length=1024)]
