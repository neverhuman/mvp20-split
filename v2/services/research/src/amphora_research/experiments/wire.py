"""Transport mapping reconstructs exact experiment aggregates before use."""
from amphora_contracts_research import (
    ExperimentDefinition,
    ExperimentExpectation,
    ExperimentProtocol,
    ExperimentReadout,
    ExperimentReplicate,
    ExperimentRevisionRef,
    ExperimentSample,
)

from ..identity.samples import SampleDefinition
from ..material_state import wire as material_wire
from .identity import ExperimentIdentity, ExperimentReference
from .model import (
    Experiment,
    MeasurementExpectation,
    ProtocolContext,
    ReadoutSpec,
    ReplicateRole,
    SampleContext,
)


def reference_to_wire(value):
    return None if value is None else ExperimentRevisionRef(scope=value.scope,experiment_id=value.experiment_id,revision=value.revision)


def reference_from_wire(record):
    return None if record is None else ExperimentReference(record.scope,record.experiment_id,record.revision)


def to_wire(plan):
    return ExperimentDefinition(wire_version="1",reference=reference_to_wire(plan.identity.reference),
        supersedes=reference_to_wire(plan.identity.supersedes),
        protocol=ExperimentProtocol(method=plan.protocol.method,applicability=plan.protocol.applicability,source=plan.protocol.source),
        samples=tuple(ExperimentSample(sample=item.sample.record,state=None if item.state is None else material_wire.to_wire(item.state)) for item in plan.samples),
        expectations=tuple(ExperimentExpectation(expectation_id=item.expectation_id,sample=item.sample,
            readout=ExperimentReadout(criterion_id=item.readout.criterion_id,kind=item.readout.kind,unit=item.readout.unit,x_unit=item.readout.x_unit),
            replicate=ExperimentReplicate(replicate_id=item.replicate.replicate_id,role=item.replicate.role)) for item in plan.expectations))


def from_wire(record):
    return Experiment(ExperimentIdentity(reference_from_wire(record.reference),reference_from_wire(record.supersedes)),
        ProtocolContext(record.protocol.method,record.protocol.applicability,record.protocol.source),
        tuple(SampleContext(SampleDefinition(item.sample),None if item.state is None else material_wire.from_wire(item.state)) for item in record.samples),
        tuple(MeasurementExpectation(item.expectation_id,item.sample,
            ReadoutSpec(item.readout.criterion_id,item.readout.kind,item.readout.unit,item.readout.x_unit),
            ReplicateRole(item.replicate.replicate_id,item.replicate.role)) for item in record.expectations))
