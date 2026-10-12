"""Read original head/profile/change; never repin to the newest graph."""
from dataclasses import dataclass
import time

from amphora_contracts_knowledge import DomainHead, GraphAuthoringProfile
from pydantic import ValidationError

from ..context.policy import require
from ..curation_context import CurationIntent
from ..campaign_context.records import canonical
from ..campaign_graph_context import CampaignGraphProjection
from ..campaign_knowledge_access import CampaignGraphSelection
from ..campaign_knowledge_access.reader import CampaignGraphResult, PEER_CODES, RECORD_CODES
from ..graph_context import GraphPins, PinnedGraphContext
from ..graph_context.origin import verify_change
from ..knowledge_access.transport import KnowledgeReadWindow


@dataclass(frozen=True)
class HeadRead:
    head: DomainHead
    result: CampaignGraphResult | None
    failure: str | None
    calls: int
    consumed: int


@dataclass(frozen=True)
class KnowledgeContext:
    intent: CurationIntent
    reads: tuple[HeadRead, ...]

    def rows(self):
        # Rebind the complete original selection before producing packet slices.
        import json
        intent = CurationIntent.from_payload(self.intent.request, json.loads(self.intent.canonical))
        selected = json.loads(intent.canonical)['command']['payload']['context']['knowledge']
        require([row.head.model_dump(mode='json') for row in self.reads] == selected, 'curation_knowledge_coverage')
        projections, summaries = [], []
        for row in self.reads:
            require((row.result is None) != (row.failure is None), 'curation_knowledge_result')
            require(type(row.calls) is int and 0 <= row.calls <= 3
                    and type(row.consumed) is int and 0 <= row.consumed <= 18087936,
                    'curation_knowledge_accounting')
            if row.result is not None:
                require(row.result.selection.request == intent.request
                        and row.result.selection.parts()[0].base == row.head, 'curation_knowledge_binding')
                projection = CampaignGraphProjection.from_result(row.result)
                value = json.loads(projection.canonical)
                projections.append(projection)
                status, reason = value['status'], value.get('reason')
            else:
                require(row.failure in PEER_CODES | {'campaign_graph_invalid', 'campaign_graph_projection_limit'},
                        'curation_knowledge_failure')
                status, reason = 'unavailable', row.failure
            summaries.append({'head': row.head.model_dump(mode='json'), 'status': status, 'reason': reason,
                              'calls': row.calls, 'bytes': row.consumed})
        summary = {'format': 'planning-curation-knowledge.v1', 'authority': 'selected_metadata_only',
                   'curation': intent.identity, 'request_sha256': intent.request.sha256,
                   'graphs': summaries, 'selection_policy': 'whole_head_or_explicit_gap'}
        return tuple(projections), summary


class CurationKnowledgeReader:
    def __init__(self, transport):
        self.transport = transport

    def read(self, intent):
        import json
        intent = CurationIntent.from_payload(intent.request, json.loads(intent.canonical))
        selected = json.loads(intent.canonical)['command']['payload']['context']['knowledge']
        heads = tuple(DomainHead.model_validate_json(canonical(item)) for item in selected)
        deadline = time.monotonic() + 30
        reads = tuple(self._head(intent.request, head, deadline) for head in heads)
        context = KnowledgeContext(intent, reads)
        context.rows()
        return context

    def _head(self, request, head, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return HeadRead(head, None, 'knowledge_read_expired', 0, 0)
        window = KnowledgeReadWindow(min(15, remaining))
        try:
            graph = head.snapshot.graph
            raw = self.transport.read('/v1/graph-profiles/read', graph, window)
            profile = GraphAuthoringProfile.model_validate_json(raw.model_dump_json())
            pins = GraphPins(graph, head, profile.vocabulary_reference, profile.policy).validated()
            snapshot = self.transport.read('/v1/graph-snapshots/read', head.snapshot, window)
            change = self.transport.read('/v1/graph-changes/read', head.change, window)
            verify_change(pins, change)
            context = PinnedGraphContext.bind(pins, profile, snapshot)
            facts = context.index()
            require(len(facts.entities) <= 256 and len(facts.assertions) <= 256, 'campaign_graph_projection_limit')
            selection = CampaignGraphSelection.bind(request, pins, tuple(facts.entities), tuple(facts.assertions))
            result = CampaignGraphResult(selection, context, None, window.calls, window.consumed)
            # Force projection limits before calling this graph available.
            projection = CampaignGraphProjection.from_result(result)
            window.remaining()
            import json
            projected = json.loads(projection.canonical)
            if projected['status'] == 'unavailable':
                return HeadRead(head, None, projected['reason'], window.calls, window.consumed)
            return HeadRead(head, result, None, window.calls, window.consumed)
        except ValueError as error:
            if isinstance(error, ValidationError) or str(error) in RECORD_CODES:
                reason = 'campaign_graph_invalid'
            elif str(error) in PEER_CODES | {'campaign_graph_projection_limit'}:
                reason = str(error)
            else:
                raise
            return HeadRead(head, None, reason, window.calls, window.consumed)
