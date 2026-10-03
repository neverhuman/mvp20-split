"""Separately granted scientific operations composed from focused owner modules."""
from ..experiments.store import ExperimentStore
from ..material_state.store import MaterialStateStore
from ..observations.intake_store import LabIntakeStore
from ..observations.store import ObservationStore
from ..persistence.decision_index import DecisionIndex
from .boundary import require
from .records import ScientificRecords
from .store import ScientificInputStore
from .workflow import LabIntakeWorkflow, ScientificAssessmentWorkflow

ACTIONS = frozenset({"submit_lab_intake","read_lab_intake","assess_eligibility","assess_synthesis",
    "read_scientific_assessment","read_scientific_record","publish_scientific_result",
    "read_scientific_publication","read_scientific_impact","register_scientific_consumer"})


class ScientificOperations:
    def __init__(self, engine, profiles, reader_factory, publications):
        self.records = ScientificRecords(engine)
        self.index = DecisionIndex(engine)
        self.materials,self.experiments,self.observations = MaterialStateStore(engine),ExperimentStore(engine),ObservationStore(engine)
        self.lab = LabIntakeWorkflow(LabIntakeStore(engine),self.experiments,profiles,reader_factory)
        self.assessments = ScientificAssessmentWorkflow(ScientificInputStore(engine),profiles,reader_factory)
        self.publications = publications

    def submit_lab(self, principal, request):
        principal.require("submit_lab_intake",request.profile.scope)
        return self.lab.submit(principal.scope,principal.actor_id,request)

    def read_lab(self, principal, request):
        principal.require("read_lab_intake",request.scope)
        return self.lab.read(principal.scope,principal.actor_id,request.intake_id)

    def submit_assessment(self, principal, request):
        principal.require("assess_"+request.profile.kind,request.profile.scope)
        return self.assessments.submit(principal.scope,principal.actor_id,request)

    def read_assessment(self, principal, request):
        principal.require("read_scientific_assessment",request.profile.scope)
        result = self.assessments.read(principal.scope,principal.actor_id,request.profile.kind,request.decision_id)
        if result is not None:
            require(result.request == request,"scientific_intent_identity_conflict")
        return result

    def read_decision(self, principal, reference):
        principal.require("read_scientific_record",reference.scope)
        return self.records.decision(principal,reference)

    def read_material(self, principal, reference):
        principal.require("read_scientific_record",reference.scope)
        return self.materials.read(principal.scope,reference)

    def read_experiment(self, principal, reference):
        principal.require("read_scientific_record",reference.scope)
        return self.experiments.read(principal.scope,reference)

    def read_observation(self, principal, reference):
        principal.require("read_scientific_record",reference.scope)
        return self.observations.read(principal.scope,reference)

    def impact(self, principal, request):
        principal.require("read_scientific_impact",request.source.scope)
        return self.index.affected(principal.scope,request.source,after=request.after,limit=request.limit)

    def consumers(self, principal, request):
        principal.require("read_scientific_impact",request.decision.scope)
        return self.index.consumers(principal.scope,request.decision,after=request.after,limit=request.limit)
