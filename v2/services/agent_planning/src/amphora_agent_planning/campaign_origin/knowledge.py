"""Selected graph context is separate from manifest Artifact references."""

import json

from amphora_contracts_knowledge import DomainGraphRef
from amphora_contracts_planning import CampaignOriginKnowledge

from ..campaign_context.records import canonical
from ..campaign_knowledge_access import CampaignGraphSelection
from ..context.policy import require


class KnowledgeOrigin:
    @classmethod
    def from_proposal(cls, prepared):
        rows = [row for row in prepared.inputs.preparation.packet.context()['slices'] if row['lane'] == 'graph']
        if not rows:
            return None
        require(len(rows) == 1, 'origin_knowledge_slice_count')
        row = rows[0]
        value = row['payload']
        require(row['identity'] == {'selection': value['selection_sha256']}, 'origin_knowledge_selection')
        retained = {(item.key.kind, item.key.identity): item.sha256 for item in prepared.inputs.entries
                    if item.key.lane == 'graph'}
        expected = {(item['kind'], canonical(item['identity'])): item['sha256'] for item in value['observations']}
        require(retained == expected, 'origin_knowledge_observations')
        return cls.bind(prepared.attempt.request, value)

    @staticmethod
    def bind(request, value):
        require(value['format'] == 'planning-campaign-graph-context.v1' and
                value['authority'] == 'selected_metadata_only' and value['request_sha256'] == request.sha256,
                'origin_knowledge_request')
        if value['status'] == 'available':
            selection = CampaignGraphSelection(request, canonical(value['selection']))
            pins, entities, assertions = selection.parts()
            verified = CampaignGraphSelection.bind(request, pins, entities, assertions)
            require(selection == verified and selection.sha256 == value['selection_sha256'], 'origin_knowledge_selection')
            return CampaignOriginKnowledge(status='available', graph=pins.graph, head=pins.base,
                vocabulary=pins.vocabulary, policy=pins.policy, entities=entities, assertions=assertions,
                selection_sha256=selection.sha256, context_sha256=value['context_sha256'], unavailable=None)
        require(value['status'] == 'unavailable' and len(value['observations']) == 1 and
                value['observations'][0]['kind'] == 'availability', 'origin_knowledge_unavailable')
        graph = DomainGraphRef.model_validate_json(json.dumps(value['observations'][0]['identity']))
        require(graph.scope == request.document().reference.scope, 'origin_knowledge_scope')
        # Older unavailable slices did not retain their head/entity selection.
        # Preserve that limitation instead of reconstructing it from a latest head.
        return CampaignOriginKnowledge(status='unavailable', graph=graph, head=None, vocabulary=None, policy=None,
            entities=(), assertions=(), selection_sha256=value['selection_sha256'], context_sha256=None,
            unavailable=value['reason'])
