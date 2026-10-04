"""Public request bytes and compiled routes; stored origin is a later boundary."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_knowledge import GraphChangeProposal, GraphProposalStatus
from amphora_contracts_research import EvidenceNeed, ResearchQuestion

from ..context.policy import require
from ..publication.records import encode
from .selection import HandoffSelection

MODELS = {"question": ResearchQuestion, "need": EvidenceNeed, "graph": GraphChangeProposal}
PATHS = {"question": "/v1/questions", "need": "/v1/evidence-needs", "graph": "/v1/graph-proposals"}


@dataclass(frozen=True)
class OwnerRequest:
    selection: HandoffSelection
    canonical: bytes

    @classmethod
    def bind(cls, selection, record):
        kind = selection.document()["kind"]
        require(type(record) is MODELS[kind], "handoff_record_kind")
        record = MODELS[kind].model_validate_json(record.model_dump_json(warnings=False))
        scope = record.graph.scope if kind == "graph" else record.reference.scope
        require(scope == selection.trace().scope, "handoff_record_scope")
        raw = encode(record.model_dump(mode="json"))
        require(len(raw) <= 262144, "handoff_request_limit")
        return cls(selection, raw)

    @property
    def kind(self):
        return self.selection.document()["kind"]

    @property
    def owner(self):
        return "knowledge" if self.kind == "graph" else "research"

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return MODELS[self.kind].model_validate_json(self.canonical)

    def submit_path(self):
        return PATHS[self.kind]

    def read_call(self):
        record = self.document()
        if self.kind == "graph":
            return "GET", f"/v1/graphs/{record.graph.graph_id}/proposals/{record.change_id}", None, GraphProposalStatus, 1048576
        return "POST", PATHS[self.kind] + "/read", encode(record.reference.model_dump(mode="json")), MODELS[self.kind], 262144
