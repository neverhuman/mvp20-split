"""Extraction-specific adapter over shared pure pinned graph records."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef
from amphora_contracts_knowledge import GraphChangeProposal

from ..context.policy import require
from ..extraction import ExtractionSnapshot
from ..graph_context import GraphPins, PinnedGraphContext
from ..graph_context.records import GraphFacts, canonical, label_key

__all__ = ['GraphFacts', 'KnowledgeContext', 'canonical', 'label_key', 'proposal_schema']


def proposal_schema():
    document = GraphChangeProposal.model_json_schema(mode="validation")
    document.update({"$schema": "https://json-schema.org/draft/2020-12/schema",
                     "$id": "urn:amphora:knowledge.proposal:1:validation"})
    raw = (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    return SchemaRef(schema_id="knowledge.proposal", version="1", sha256=hashlib.sha256(raw).hexdigest())


@dataclass(frozen=True)
class KnowledgeContext:
    task_sha256: str
    profile_bytes: bytes
    snapshot_bytes: bytes | None

    @classmethod
    def bind(cls, task, profile, snapshot):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        target = task.document().target
        require(target.operation_schema == proposal_schema(), "graph_operation_profile")
        if target.base is None:
            require(snapshot is None and not task.document().existing_entities and
                    not getattr(task.document(), "existing_assertions", ()), "graph_genesis_binding")
        context = PinnedGraphContext.bind(GraphPins(target.graph, target.base, target.vocabulary, target.policy), profile, snapshot)
        return cls(task.sha256, context.profile_bytes, context.snapshot_bytes)

    def profile(self):
        return PinnedGraphContext(self.profile_bytes, self.snapshot_bytes).profile()

    def snapshot(self):
        return PinnedGraphContext(self.profile_bytes, self.snapshot_bytes).snapshot()

    def index(self):
        return PinnedGraphContext(self.profile_bytes, self.snapshot_bytes).index()
