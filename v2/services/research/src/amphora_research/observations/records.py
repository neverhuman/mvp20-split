"""Reported bindings and quality are preserved independently from matching or scientific use."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_research import MaterialStateRevisionRef, SampleRevisionRef

from ..experiments.identity import ExperimentReference
from .identity import ObservationIdentity, identifier, require
from .series import SeriesValue
from .values import CategoryValue, CensoredValue, MissingValue, NumericValue


@dataclass(frozen=True, slots=True)
class ReturnTarget:
    experiment: ExperimentReference | None
    expectation_id: str | None
    replicate_id: str | None

    def __post_init__(self):
        require(self.experiment is None or type(self.experiment) is ExperimentReference,"return_experiment_type")
        for name in (self.expectation_id,self.replicate_id):
            if name is not None:
                identifier(name)


@dataclass(frozen=True, slots=True)
class SpecimenClaim:
    sample: SampleRevisionRef | None
    material_state: MaterialStateRevisionRef | None

    def __post_init__(self):
        require(self.sample is None or type(self.sample) is SampleRevisionRef,"return_sample_type")
        require(self.material_state is None or type(self.material_state) is MaterialStateRevisionRef,"return_state_type")


@dataclass(frozen=True, slots=True)
class MethodClaim:
    method: SchemaRef | None
    context: ArtifactRef | None

    def __post_init__(self):
        require(self.method is None or type(self.method) is SchemaRef,"return_method_type")
        require(self.context is None or type(self.context) is ArtifactRef,"return_context_type")


@dataclass(frozen=True, slots=True)
class ObservationBinding:
    target: ReturnTarget
    specimen: SpecimenClaim
    measurement: MethodClaim
    role: str | None

    def __post_init__(self):
        require(type(self.target) is ReturnTarget,"return_target_required")
        require(type(self.specimen) is SpecimenClaim,"specimen_claim_required")
        require(type(self.measurement) is MethodClaim,"method_claim_required")
        require(self.role in (None,"sample","positive_control","negative_control","blank"),"return_role_invalid")


@dataclass(frozen=True, slots=True)
class ReportedQuality:
    controls: str
    flags: tuple[str, ...]

    def __post_init__(self):
        require(self.controls in ("passed","failed","unknown"),"reported_control_status_invalid")
        require(type(self.flags) is tuple and len(self.flags) <= 64,"reported_flag_bound")
        for flag in self.flags:
            identifier(flag)
        require(len(set(self.flags)) == len(self.flags),"duplicate_reported_flag")


@dataclass(frozen=True, slots=True)
class Observation:
    identity: ObservationIdentity
    source: ArtifactRef
    binding: ObservationBinding
    value: NumericValue | CensoredValue | CategoryValue | MissingValue | SeriesValue
    quality: ReportedQuality

    def __post_init__(self):
        require(type(self.identity) is ObservationIdentity,"observation_identity_required")
        require(type(self.source) is ArtifactRef,"observation_source_required")
        require(self.source.scope == self.identity.reference.scope,"observation_source_scope_mismatch")
        require(type(self.binding) is ObservationBinding,"observation_binding_required")
        require(type(self.value) in (NumericValue,CensoredValue,CategoryValue,MissingValue,SeriesValue),"observation_value_required")
        require(type(self.quality) is ReportedQuality,"reported_quality_required")

    @property
    def value_available(self):
        return self.value.reported_count > 0 if type(self.value) is SeriesValue else type(self.value) is not MissingValue
