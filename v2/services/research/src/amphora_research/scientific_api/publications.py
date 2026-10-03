"""Artifact publication and authenticated explicit consumer links; no Runtime authority."""
from amphora_contracts_research import (
    ScientificDecisionSelection,
    ScientificPublicationComplete,
    ScientificPublicationFailed,
    ScientificPublicationPending,
    ScientificPublicationStatus,
)

from ..assessment.resolution import require_inputs
from ..persistence.decision_index import DecisionIndex
from ..scientific_publication.store import ScientificPublicationStore
from ..scientific_publication.workflow import ScientificPublicationWorkflow
from .boundary import require
from .records import ScientificRecords, selection_scope


class ScientificPublications:
    def __init__(self, engine, reader_factory, transport_factory, publisher, consumer_publishers):
        self.records = ScientificRecords(engine)
        self.store = ScientificPublicationStore(engine)
        self.index = DecisionIndex(engine)
        self.reader_factory,self.transport_factory = reader_factory,transport_factory
        self.publisher,self.consumer_publishers = publisher,frozenset(consumer_publishers)

    @staticmethod
    def status(request, artifact, progress):
        if progress is None:
            return None
        if progress.stage == "published":
            outcome = ScientificPublicationComplete(status="published",derivation=progress.derivation)
        elif progress.stage == "failed":
            outcome = ScientificPublicationFailed(status="failed",code=progress.failure,external_effects="possible")
        else:
            outcome = ScientificPublicationPending(status="pending")
        return ScientificPublicationStatus(wire_version="1",request=request,actor_id=artifact.document.actor_id,outcome=outcome)

    def read(self, principal, request):
        principal.require("read_scientific_publication",selection_scope(request.target))
        artifact = self.records.artifact(principal,request.target)
        return self.status(request,artifact,self.store.lookup(artifact))

    def submit(self, principal, request):
        principal.require("publish_scientific_result",selection_scope(request.target))
        artifact = self.records.artifact(principal,request.target)
        progress = self.store.lookup(artifact)
        if progress is None or progress.stage not in ("published","failed"):
            publisher = self.publisher if progress is None else progress.publisher
            workflow = ScientificPublicationWorkflow(self.store,self.reader_factory(principal.scope),self.transport_factory(),publisher)
            progress = workflow.submit(artifact)
        return self.status(request,artifact,progress)

    def register_consumer(self, principal, request):
        principal.require("register_scientific_consumer",request.decision.scope)
        require(request.consumer.scope == principal.scope,"scientific_consumer_scope")
        artifact = self.records.artifact(principal,ScientificDecisionSelection(kind="decision",reference=request.decision))
        progress = self.store.lookup(artifact)
        require(progress is not None and progress.stage == "published","scientific_consumer_publication_pending")
        reader = self.reader_factory(principal.scope)
        require(not reader.consumed,"scientific_input_reader_reused")
        _,proof = reader.published(request.consumer,self.consumer_publishers)
        require_inputs(proof,(progress.derivation.artifact,))
        reader.read(progress.derivation.artifact)
        return self.index.register_consumer(principal.scope,principal.actor_id,request.decision,request.consumer)
