"""Bounded generation advancement and retrieval facade; no transport-owned authority."""

from ..representations.storage.records import authorize
from .intents import GenerationIntents
from .leases import GenerationBusy, GenerationLease, GenerationLeases
from .publication import GenerationPublication
from .queries.broker import RetrievalBroker
from .validation import require


class RetrievalService:
    def __init__(self, reads, backend):
        self.intents = GenerationIntents(reads.engine, backend.reference)
        self.leases = GenerationLeases(reads.engine)
        self.publication = GenerationPublication(reads, backend)
        self.queries = RetrievalBroker(reads, backend)

    def advance(self, principal, request):
        authorize(principal, "representation_manage")
        principal.require("representation_read")
        principal.require("read")
        status = self.intents.prepare(principal, request)
        if status.state in {"published", "failed", "abandoned"}:
            return status
        claim = self.leases.claim(principal, request.corpus_id, request.generation_id)
        if type(claim) is GenerationBusy:
            return self.intents.read(principal, request.corpus_id, request.generation_id)
        if type(claim) is not GenerationLease:
            return claim
        self.publication.build_and_verify(principal, claim)
        return self.publication.publish(principal, claim)

    def generation(self, principal, corpus_id, generation_id, sha256):
        status = self.intents.read(principal, corpus_id, generation_id)
        require(status.generation.reference.sha256 == sha256, "retrieval_generation_conflict")
        return status
