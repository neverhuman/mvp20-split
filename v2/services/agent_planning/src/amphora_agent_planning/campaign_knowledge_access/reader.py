"""Exact historical graph reads; technical failures do not veto other context."""

from dataclasses import dataclass

from pydantic import ValidationError

from ..context.policy import require
from ..graph_context import PinnedGraphContext
from ..graph_context.origin import verify_change
from ..knowledge_access.transport import PROFILE, KnowledgeReadWindow
from .selection import CampaignGraphSelection

PEER_CODES = frozenset('knowledge_' + suffix for suffix in (
    'access_denied', 'reference_unavailable', 'peer_unavailable', 'peer_media', 'response_limit',
    'peer_protocol', 'read_expired', 'read_call_limit', 'read_byte_limit'))
RECORD_CODES = frozenset({
    'graph_profile_binding', 'graph_vocabulary_duplicate', 'graph_vocabulary_endpoints', 'graph_vocabulary_digest',
    'graph_profile_size', 'graph_genesis_binding', 'graph_snapshot_missing', 'graph_snapshot_binding', 'graph_snapshot_digest',
    'graph_snapshot_size', 'graph_record_identity', 'graph_alias_identity', 'graph_retraction_identity',
    'graph_assertion_endpoints', 'unknown_entity_revision', 'graph_alias_cycle', 'knowledge_change_digest',
    'knowledge_change_binding', 'knowledge_selected_entity_missing', 'knowledge_selected_assertion_missing',
})


@dataclass(frozen=True)
class CampaignGraphResult:
    selection: CampaignGraphSelection
    context: PinnedGraphContext | None
    failure: str | None
    calls: int
    bytes: int


class CampaignKnowledgeReader:
    def __init__(self, knowledge):
        self.knowledge = knowledge

    def read(self, selection, window=None):
        selection = CampaignGraphSelection.bind(selection.request, *selection.parts())
        pins, entities, assertions = selection.parts()
        window = KnowledgeReadWindow() if window is None else window
        require(window.profile == PROFILE, 'knowledge_read_profile_mismatch')
        calls, consumed = window.calls, window.consumed
        context, failure = None, None
        try:
            profile = self.knowledge.read('/v1/graph-profiles/read', pins.graph, window)
            snapshot = None
            if pins.base is not None:
                snapshot = self.knowledge.read('/v1/graph-snapshots/read', pins.base.snapshot, window)
                change = self.knowledge.read('/v1/graph-changes/read', pins.base.change, window)
                verify_change(pins, change)
            candidate = PinnedGraphContext.bind(pins, profile, snapshot)
            facts = candidate.index()
            require(all(ref in facts.entities for ref in entities), 'knowledge_selected_entity_missing')
            require(all(ref in facts.assertions for ref in assertions), 'knowledge_selected_assertion_missing')
            window.remaining()
            context = candidate
        except ValueError as error:
            if isinstance(error, ValidationError) or str(error) in RECORD_CODES:
                failure = 'campaign_graph_invalid'
            elif str(error) in PEER_CODES:
                failure = str(error)
            else:
                raise
        return CampaignGraphResult(selection, context, failure, window.calls - calls, window.consumed - consumed)
