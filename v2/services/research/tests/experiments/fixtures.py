"""Synthetic identities only; no claim of physical preparation or assay validity."""
from amphora_contracts_research import SampleIdentity, SampleRevisionRef
from amphora_research.experiments.identity import ExperimentIdentity, ExperimentReference
from amphora_research.experiments.model import (
    Experiment,
    MeasurementExpectation,
    ProtocolContext,
    ReadoutSpec,
    ReplicateRole,
    SampleContext,
)
from amphora_research.identity.samples import SampleDefinition
from amphora_research.material_state.preparation import PreparationHistory
from amphora_research.material_state.state import MaterialState

from ..material_state.test_context import CANDIDATE, METHOD, SCOPE, artifact, identity


def specimen(known=True):
    state = MaterialState(identity(),PreparationHistory(()),()) if known else None
    record = SampleIdentity(wire_version="1",reference=SampleRevisionRef(scope=SCOPE,sample_id="vial",revision=1),
        candidate=CANDIDATE,material_state=state.identity.reference if state else None,
        identity_evidence=artifact("identity"),supersedes=None)
    return SampleContext(SampleDefinition(record),state)


def experiment(known=True,kind="numeric",unit="mg/L",x_unit=None):
    sample = specimen(known)
    return Experiment(ExperimentIdentity(ExperimentReference(SCOPE,"assay",1),None),
        ProtocolContext(METHOD,artifact("context"),artifact("protocol")),(sample,),
        (MeasurementExpectation("readout",sample.sample.record.reference,ReadoutSpec("concentration",kind,unit,x_unit),
          ReplicateRole("replicate-1","sample")),))
