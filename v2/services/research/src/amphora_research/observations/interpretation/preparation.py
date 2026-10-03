"""Exact owned inputs and complete explicit evidence dependencies; no inferred head selection."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import ExperimentDefinition, ObservationRevision
from sqlalchemy import text

from ...experiments import wire as experiment_wire
from .. import wire as observation_wire
from ..identity import require
from .document import InterpretationDocument


def read_owned(connection, reference, kind):
    # Table selection is closed and private, never interpolated from caller text.
    table,field,model = {"observation":("observation_revisions","observation_id",ObservationRevision),
        "experiment":("experiment_revisions","experiment_id",ExperimentDefinition)}[kind]
    key = {"tenant":reference.scope.tenant_id,"project":reference.scope.project_id,
        "id":getattr(reference,field),"revision":reference.revision}
    raw = connection.execute(text(f"SELECT canonical_bytes FROM research.{table} "
        "WHERE tenant_id=:tenant AND project_id=:project AND identity_id=:id AND revision=:revision"),key).scalar_one_or_none()
    require(raw is not None,"interpretation_unknown_"+kind)
    return model.model_validate_json(bytes(raw))


@dataclass(frozen=True, slots=True)
class PreparedInterpretation:
    intent: object
    observations: tuple
    experiment: object | None
    sources: tuple[ArtifactRef, ...]

    @classmethod
    def load(cls, connection, intent):
        request = intent.request
        references = (request.observation,) if intent.profile.kind == "normalization" else request.observations
        observations = tuple(observation_wire.from_wire(read_owned(connection,ref,"observation")) for ref in references)
        experiment = None if intent.profile.kind == "normalization" else experiment_wire.from_wire(read_owned(connection,request.experiment,"experiment"))
        sources = [row.source for row in observations]
        if experiment is not None:
            sources.extend((experiment.protocol.source,experiment.protocol.applicability))
            for sample in experiment.samples:
                sources.append(sample.sample.record.identity_evidence)
                if sample.state is not None:
                    sources.extend(event.attribution.source for event in sample.state.preparation.events)
                    sources.extend(feature.evidence.source for feature in sample.state.features if feature.evidence.source is not None)
        require(all(item.scope == intent.profile.scope for item in sources),"interpretation_dependency_scope")
        sources = tuple(sorted(set(sources),key=lambda item:item.artifact_id))
        require(len(sources) <= 128,"interpretation_dependency_limit")
        require(len({item.artifact_id for item in sources}) == len(sources),"interpretation_dependency_conflict")
        return cls(intent,observations,experiment,sources)

    @property
    def material_states(self):
        if self.experiment is None:
            return ()
        return tuple(sorted({sample.state.identity.reference for sample in self.experiment.samples if sample.state is not None},
            key=lambda ref:(ref.material_state_id,ref.revision)))

    def document(self, consumed):
        require(type(consumed) is tuple and len(consumed) <= 128,"interpretation_consumed_limit")
        require(all(type(item) is ArtifactRef for item in consumed),"interpretation_consumed_reference")
        require(set(self.sources) <= set(consumed),"interpretation_dependency_missing")
        return InterpretationDocument.prepare(self.intent.profile,self.intent.request,self.intent.actor,
            self.observations,self.experiment,consumed)
