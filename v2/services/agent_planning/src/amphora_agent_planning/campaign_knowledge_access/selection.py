"""Immutable original-request graph selection, without an extraction task."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_knowledge import (
    AssertionRevisionRef,
    DomainGraphRef,
    DomainHead,
    EntityRevisionRef,
    StructuralPolicyRef,
    VocabularyRef,
)

from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..graph_context import GraphPins


@dataclass(frozen=True)
class CampaignGraphSelection:
    request: RequestSnapshot
    canonical: bytes

    @classmethod
    def bind(cls, request, pins, entities=(), assertions=()):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {'campaign_proposal', 'supervision'}, 'campaign_graph_purpose')
        pins = pins.validated()
        require(pins.graph.scope == original.reference.scope, 'campaign_graph_scope')
        groups = []
        for values, model in ((entities, EntityRevisionRef), (assertions, AssertionRevisionRef)):
            require(type(values) is tuple and len(values) <= 256, 'campaign_graph_count')
            values = tuple(model.model_validate(value.model_dump(mode='python', warnings=False)) for value in values)
            require(all(value.graph == pins.graph for value in values), 'campaign_graph_scope')
            require(len(set(values)) == len(values), 'campaign_graph_duplicate')
            groups.append([value.model_dump(mode='json') for value in values])
        require(pins.base is not None or not (entities or assertions), 'campaign_graph_genesis')
        value = {name: None if item is None else item.model_dump(mode='json') for name, item in
                 (('graph', pins.graph), ('base', pins.base), ('vocabulary', pins.vocabulary), ('policy', pins.policy))}
        value.update(entities=groups[0], assertions=groups[1])
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
        require(len(raw) <= 262144, 'campaign_graph_size')
        return cls(request, raw)

    def parts(self):
        require(type(self.canonical) is bytes and len(self.canonical) <= 262144, 'campaign_graph_size')
        value = json.loads(self.canonical, object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {'graph', 'base', 'vocabulary', 'policy', 'entities', 'assertions'},
                'campaign_graph_shape')
        require(type(value['entities']) is list and type(value['assertions']) is list and
                len(value['entities']) <= 256 and len(value['assertions']) <= 256, 'campaign_graph_count')
        pins = GraphPins(DomainGraphRef.model_validate(value['graph']),
                         None if value['base'] is None else DomainHead.model_validate(value['base']),
                         VocabularyRef.model_validate(value['vocabulary']), StructuralPolicyRef.model_validate(value['policy']))
        return pins, tuple(EntityRevisionRef.model_validate(ref) for ref in value['entities']), tuple(
            AssertionRevisionRef.model_validate(ref) for ref in value['assertions'])

    @property
    def sha256(self):
        return hashlib.sha256(b'planning-campaign-graph.v1\n' + self.request.sha256.encode('ascii') + b'\n' + self.canonical).hexdigest()
