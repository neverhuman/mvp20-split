"""Explicit scoped grants for computation, immutable history and known correction impacts."""
from ..material_state.correction_views import MaterialStateCorrectionViews
from ..observations.correction_views import ObservationCorrectionViews
from ..observations.interpretation.index import InterpretationIndex
from ..observations.interpretation.store import InterpretationStore
from ..persistence.material_impact import MaterialDecisionIndex
from .workflow import InterpretationWorkflow

ACTIONS = frozenset({"normalize_observation","assess_observation_use","read_observation_interpretation","read_interpretation_impact"})


class InterpretationOperations:
    def __init__(self, engine, profiles, reader_factory):
        self.workflow = InterpretationWorkflow(InterpretationStore(engine),profiles,reader_factory)
        self.observations = ObservationCorrectionViews(engine)
        self.materials = MaterialStateCorrectionViews(engine)
        self.material_index = MaterialDecisionIndex(engine)
        self.index = InterpretationIndex(engine)

    def normalize(self, principal, request):
        principal.require("normalize_observation",request.profile.scope)
        return self.workflow.submit(principal.scope,principal.actor_id,request)

    def assess_use(self, principal, request):
        principal.require("assess_observation_use",request.profile.scope)
        return self.workflow.submit(principal.scope,principal.actor_id,request)

    def read(self, principal, request):
        principal.require("read_observation_interpretation",request.scope)
        return self.workflow.read(principal.scope,principal.actor_id,request.kind,request.interpretation_id)

    def observation_correction(self, principal, successor):
        principal.require("read_scientific_record",successor.scope)
        return self.observations.read(principal.scope,successor)

    def material_correction(self, principal, successor):
        principal.require("read_scientific_record",successor.scope)
        return self.materials.read(principal.scope,successor)

    def material_impact(self, principal, request):
        principal.require("read_scientific_impact",request.source.scope)
        return self.material_index.affected(principal.scope,request.source,after=request.after,limit=request.limit)

    def interpretation_impact(self, principal, request):
        principal.require("read_interpretation_impact",request.source.scope)
        return self.index.affected(principal.scope,request.source,after=request.after,limit=request.limit)
