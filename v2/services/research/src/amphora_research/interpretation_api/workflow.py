"""Authenticate every new-use dependency after pinning intent; history replays without peer reads."""
from amphora_contracts_core import Scope
from amphora_contracts_research import AssessObservationUseRequest, NormalizeObservationRequest

from ..observations.identity import identifier, require
from .status import to_wire


class InterpretationWorkflow:
    def __init__(self, store, profiles, reader_factory):
        self.store,self.profiles,self.reader_factory = store,profiles,reader_factory

    def submit(self, scope, actor, request):
        require(type(request) in (NormalizeObservationRequest,AssessObservationUseRequest),"interpretation_request_required")
        request = type(request).model_validate_json(request.model_dump_json())
        identifier(actor)
        require(type(scope) is Scope and scope == request.profile.scope,"interpretation_scope_mismatch")
        existing = self.store.read(scope,actor,request.kind,request.interpretation_id)
        if existing is None:
            profile = self.profiles.select(request.profile)
            accepted = self.store.begin(profile,request,actor)
        else:
            require(existing.intent.request == request,"interpretation_intent_conflict")
            accepted = existing
        if accepted.result is not None:
            return to_wire(accepted)
        prepared = self.store.prepare(accepted.intent)
        reader = self.reader_factory(scope)
        require(reader.scope == scope and not reader.consumed,"interpretation_reader_scope_or_reuse")
        for source in prepared.sources:
            reader.read(source)
        # Store completion checks the complete exact required source set and owned
        # inputs again. Only a fresh authenticated reader belongs at this boundary.
        return to_wire(self.store.complete(prepared,reader.consumed))

    def read(self, scope, actor, kind, interpretation_id):
        return to_wire(self.store.read(scope,actor,kind,interpretation_id))
