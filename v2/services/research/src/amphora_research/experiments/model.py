"""Exact specimen/context expectations retain unknown material state without inventing it."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_research import SampleRevisionRef

from ..identity.samples import SampleDefinition
from ..material_state.state import MaterialState
from ..observations.quantities import unit_token
from .identity import ExperimentIdentity, identifier, require


@dataclass(frozen=True, slots=True)
class SampleContext:
    sample: SampleDefinition
    state: MaterialState | None

    def __post_init__(self):
        require(type(self.sample) is SampleDefinition,"experiment_sample_required")
        if self.state is not None:
            require(type(self.state) is MaterialState,"experiment_state_type")
            require(self.sample.record.material_state == self.state.identity.reference,"sample_state_mismatch")
            require(self.sample.record.candidate == self.state.identity.candidate,"sample_state_candidate_mismatch")


@dataclass(frozen=True, slots=True)
class ProtocolContext:
    method: SchemaRef
    applicability: ArtifactRef
    source: ArtifactRef

    def __post_init__(self):
        require(type(self.method) is SchemaRef,"experiment_method_required")
        require(type(self.applicability) is ArtifactRef and type(self.source) is ArtifactRef,"experiment_context_required")
        require(self.applicability.scope == self.source.scope,"experiment_context_scope_mismatch")


@dataclass(frozen=True, slots=True)
class ReadoutSpec:
    criterion_id: str
    kind: str
    unit: str | None
    x_unit: str | None = None

    def __post_init__(self):
        identifier(self.criterion_id)
        require(self.kind in ("numeric","categorical","series"),"invalid_readout_kind")
        if self.kind == "categorical":
            require(self.unit is None,"categorical_readout_has_unit")
        else:
            unit_token(self.unit)
        if self.kind == "series":
            unit_token(self.x_unit)
        else:
            require(self.x_unit is None,"unexpected_readout_axis")


@dataclass(frozen=True, slots=True)
class ReplicateRole:
    replicate_id: str
    role: str

    def __post_init__(self):
        identifier(self.replicate_id)
        require(self.role in ("sample","positive_control","negative_control","blank"),"invalid_replicate_role")


@dataclass(frozen=True, slots=True)
class MeasurementExpectation:
    expectation_id: str
    sample: SampleRevisionRef
    readout: ReadoutSpec
    replicate: ReplicateRole

    def __post_init__(self):
        identifier(self.expectation_id)
        require(type(self.sample) is SampleRevisionRef,"expectation_sample_required")
        require(type(self.readout) is ReadoutSpec,"readout_spec_required")
        require(type(self.replicate) is ReplicateRole,"replicate_role_required")


@dataclass(frozen=True, slots=True)
class Experiment:
    identity: ExperimentIdentity
    protocol: ProtocolContext
    samples: tuple[SampleContext, ...]
    expectations: tuple[MeasurementExpectation, ...]

    def __post_init__(self):
        require(type(self.identity) is ExperimentIdentity,"experiment_identity_required")
        require(type(self.protocol) is ProtocolContext,"protocol_context_required")
        scope = self.identity.reference.scope
        require(self.protocol.source.scope == scope,"experiment_protocol_scope_mismatch")
        require(type(self.samples) is tuple and 1 <= len(self.samples) <= 256,"experiment_sample_bound")
        require(all(type(item) is SampleContext for item in self.samples),"sample_context_required")
        refs = tuple(item.sample.record.reference for item in self.samples)
        require(all(ref.scope == scope for ref in refs),"experiment_sample_scope_mismatch")
        require(len(set(refs)) == len(refs),"duplicate_experiment_sample")
        require(type(self.expectations) is tuple and 1 <= len(self.expectations) <= 1024,"expectation_bound")
        require(all(type(item) is MeasurementExpectation for item in self.expectations),"measurement_expectation_required")
        require(len({item.expectation_id for item in self.expectations}) == len(self.expectations),"duplicate_expectation")
        require(all(item.sample in refs for item in self.expectations),"expectation_sample_unbound")

    def expectation(self, expectation_id):
        return next((item for item in self.expectations if item.expectation_id == expectation_id),None)

    def sample(self, reference):
        return next((item for item in self.samples if item.sample.record.reference == reference),None)
