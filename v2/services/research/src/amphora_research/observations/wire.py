"""Reported values/bindings survive wire mapping without acceptance or reinterpretation."""
from amphora_contracts_research import (
    ObservationBindingRecord,
    ObservationMethod,
    ObservationQuality,
    ObservationRevision,
    ObservationRevisionRef,
    ObservationSpecimen,
    ObservationTarget,
)

from ..experiments import wire as experiment_wire
from . import measurement_wire
from .identity import ObservationIdentity, ObservationReference
from .records import (
    MethodClaim,
    Observation,
    ObservationBinding,
    ReportedQuality,
    ReturnTarget,
    SpecimenClaim,
)


def reference_to_wire(value):
    return None if value is None else ObservationRevisionRef(scope=value.scope,observation_id=value.observation_id,revision=value.revision)


def reference_from_wire(record):
    return None if record is None else ObservationReference(record.scope,record.observation_id,record.revision)


def to_wire(value):
    binding = value.binding
    return ObservationRevision(wire_version="1",reference=reference_to_wire(value.identity.reference),
        supersedes=reference_to_wire(value.identity.supersedes),source=value.source,
        binding=ObservationBindingRecord(target=ObservationTarget(experiment=experiment_wire.reference_to_wire(binding.target.experiment),
            expectation_id=binding.target.expectation_id,replicate_id=binding.target.replicate_id),
            specimen=ObservationSpecimen(sample=binding.specimen.sample,material_state=binding.specimen.material_state),
            measurement=ObservationMethod(method=binding.measurement.method,context=binding.measurement.context),role=binding.role),
        value=measurement_wire.to_wire(value.value),quality=ObservationQuality(controls=value.quality.controls,flags=value.quality.flags))


def from_wire(record):
    binding = record.binding
    return Observation(ObservationIdentity(reference_from_wire(record.reference),reference_from_wire(record.supersedes)),record.source,
        ObservationBinding(ReturnTarget(experiment_wire.reference_from_wire(binding.target.experiment),binding.target.expectation_id,binding.target.replicate_id),
            SpecimenClaim(binding.specimen.sample,binding.specimen.material_state),
            MethodClaim(binding.measurement.method,binding.measurement.context),binding.role),
        measurement_wire.from_wire(record.value),ReportedQuality(record.quality.controls,record.quality.flags))
