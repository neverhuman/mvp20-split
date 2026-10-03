"""Private orchestration persists pinned intent before peers; failures are not scientific verdicts."""
from amphora_contracts_core import Scope
from amphora_contracts_research import LabIntakeRequest, ScientificAssessmentRequest

from ..observations.intake import IntakeIntent
from ..observations.resolution import LabReportResolver
from .boundary import IDENTIFIER, require
from .resolution import ScientificInputResolver


class ScientificAssessmentWorkflow:
    def __init__(self, store, profiles, reader_factory):
        self.store,self.profiles,self.reader_factory = store,profiles,reader_factory

    def submit(self, scope, actor, request):
        require(type(request) is ScientificAssessmentRequest,"scientific_input_request_type")
        request = ScientificAssessmentRequest.model_validate_json(request.model_dump_json())
        IDENTIFIER.validate_python(actor,strict=True)
        require(type(scope) is Scope and request.profile.scope == scope,"scientific_input_scope_mismatch")
        existing = self.store.read(scope,actor,request.profile.kind,request.decision_id)
        if existing is None:
            configured = self.profiles.select(request.profile)
            accepted = self.store.begin(configured.bind(request,actor,scope))
        else:
            require(existing.intent.bound.request == request,"scientific_intent_identity_conflict")
            accepted = existing
        if accepted.decision is not None:
            return accepted.status
        bound = accepted.intent.bound
        resolved = ScientificInputResolver(self.reader_factory(scope)).resolve(bound)
        return self.store.complete(bound,resolved).status

    def read(self, scope, actor, kind, decision_id):
        result = self.store.read(scope,actor,kind,decision_id)
        return None if result is None else result.status


class LabIntakeWorkflow:
    def __init__(self, store, experiments, profiles, reader_factory):
        self.store,self.experiments = store,experiments
        self.profiles,self.reader_factory = profiles,reader_factory

    def submit(self, scope, actor, request):
        require(type(request) is LabIntakeRequest,"lab_intake_request_required")
        request = LabIntakeRequest.model_validate_json(request.model_dump_json())
        IDENTIFIER.validate_python(actor,strict=True)
        require(type(scope) is Scope and request.profile.scope == scope,"lab_intake_scope_mismatch")
        existing = self.store.read(scope,actor,request.intake_id)
        if existing is None:
            configured = self.profiles.select(request.profile)
            accepted = self.store.begin(IntakeIntent.bind(configured,request,actor,scope))
        else:
            require(existing.intent.request == request,"lab_intake_identity_conflict")
            accepted = existing
        if accepted.terminal is not None:
            return accepted.status
        intent = accepted.intent
        reader = self.reader_factory(scope)
        require(not reader.consumed,"lab_input_reader_reused")
        resolved = LabReportResolver(self.experiments,reader).resolve(intent.configured,intent.request.report)
        return self.store.complete(intent,resolved).status

    def read(self, scope, actor, intake_id):
        result = self.store.read(scope,actor,intake_id)
        return None if result is None else result.status
