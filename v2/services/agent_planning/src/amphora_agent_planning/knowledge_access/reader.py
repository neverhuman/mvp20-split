"""Bind public owner reads to an immutable task without reading a newer head."""

from ..context.policy import require
from ..extraction import ExtractionSnapshot
from ..graph_context import GraphPins
from ..graph_context.origin import verify_change
from ..proposals.context import KnowledgeContext
from .transport import KnowledgeReadWindow


class KnowledgeReader:
    def __init__(self, transport):
        self.transport = transport

    def review(self, task, window=None):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        window = KnowledgeReadWindow() if window is None else window
        target = task.document().target
        profile = self.transport.read('/v1/graph-profiles/read', target.graph, window)
        snapshot = None
        if target.base is not None:
            snapshot = self.transport.read('/v1/graph-snapshots/read', target.base.snapshot, window)
            change = self.transport.read('/v1/graph-changes/read', target.base.change, window)
            verify_change(GraphPins(target.graph, target.base, target.vocabulary, target.policy), change)
        result = KnowledgeContext.bind(task, profile, snapshot)
        facts = result.index()
        require(all(ref in facts.entities for ref in task.document().existing_entities), 'knowledge_selected_entity_missing')
        require(all(ref in facts.assertions for ref in getattr(task.document(), 'existing_assertions', ())),
                'knowledge_selected_assertion_missing')
        window.remaining()
        return result
