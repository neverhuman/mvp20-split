"""Bind public owner reads to an immutable task without reading a newer head."""

import hashlib

from ..context.policy import require
from ..extraction import ExtractionSnapshot
from ..proposals.context import KnowledgeContext, canonical
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
            content = change.content
            require(change.reference == target.base.change and
                    hashlib.sha256(canonical(content)).hexdigest() == change.reference.sha256,
                    'knowledge_change_digest')
            require(content.resulting_snapshot == target.base.snapshot and
                    content.position == target.base.change.position and content.policy == target.policy and
                    content.proposal.graph == target.graph and content.proposal.change_id == change.reference.change_id and
                    content.proposal.policy == target.policy and content.proposal.vocabulary == target.vocabulary,
                    'knowledge_change_binding')
        result = KnowledgeContext.bind(task, profile, snapshot)
        facts = result.index()
        require(all(ref in facts.entities for ref in task.document().existing_entities), 'knowledge_selected_entity_missing')
        require(all(ref in facts.assertions for ref in getattr(task.document(), 'existing_assertions', ())),
                'knowledge_selected_assertion_missing')
        window.remaining()
        return result
