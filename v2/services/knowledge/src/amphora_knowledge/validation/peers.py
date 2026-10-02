"""Only public versioned Data and Research routes and DTOs cross this boundary."""

from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import ConversionTrace, SourceRevision
from amphora_contracts_research import EvidenceNeed, ResearchQuestion

from ..authoring.canonical import KnowledgeError


class DataReader:
    def __init__(self, transport):
        self.transport = transport

    def artifact(self, reference, budget):
        return self.transport.record(f"/v1/artifacts/{reference.artifact_id}", ArtifactRef, budget)

    def content(self, reference, budget):
        if reference.size_bytes > 4 * 1024 * 1024:
            raise KnowledgeError("artifact_read_limit")
        return self.transport.read(f"/v1/artifacts/{reference.artifact_id}/content", budget,
            limit=reference.size_bytes, json_body=False)

    def source(self, reference, budget):
        return self.transport.record(f"/v1/acquisition/sources/{reference.source_id}/{reference.revision_id}",
            SourceRevision, budget)

    def trace(self, reference, budget):
        return self.transport.record(f"/v1/acquisition/traces/{reference.trace_id}", ConversionTrace, budget)


class ResearchReader:
    def __init__(self, transport):
        self.transport = transport

    def question(self, reference, budget):
        return self.transport.record("/v1/questions/read", ResearchQuestion, budget, query=reference)

    def need(self, reference, budget):
        return self.transport.record("/v1/evidence-needs/read", EvidenceNeed, budget, query=reference)
