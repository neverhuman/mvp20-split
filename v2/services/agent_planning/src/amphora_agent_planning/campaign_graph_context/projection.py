"""Exact selected graph data and relevant observations, never graph acceptance."""

import hashlib
import json
from dataclasses import dataclass

from ..campaign_knowledge_access import CampaignGraphSelection
from ..campaign_knowledge_access.reader import PEER_CODES
from ..context.policy import require
from ..graph_context import PinnedGraphContext


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def wire(value):
    return value.model_dump(mode='json')


@dataclass(frozen=True)
class GraphObservation:
    kind: str
    identity: bytes
    sha256: str

    @classmethod
    def capture(cls, kind, identity, value):
        require(kind in {'availability', 'profile', 'entity', 'assertion', 'alias', 'retraction'}, 'campaign_graph_observation_kind')
        return cls(kind, encode(identity), hashlib.sha256(encode(value)).hexdigest())


@dataclass(frozen=True)
class CampaignGraphProjection:
    selection: CampaignGraphSelection
    canonical: bytes
    observations: tuple[GraphObservation, ...]

    @classmethod
    def unavailable(cls, selection, reason):
        selection = CampaignGraphSelection.bind(selection.request, *selection.parts())
        require(reason in PEER_CODES | {'campaign_graph_invalid', 'campaign_graph_projection_limit'}, 'campaign_graph_unavailable_reason')
        value = {'format': 'planning-campaign-graph-context.v1', 'request_sha256': selection.request.sha256,
            'selection_sha256': selection.sha256, 'authority': 'selected_metadata_only', 'status': 'unavailable', 'reason': reason}
        observation = GraphObservation.capture('availability', wire(selection.parts()[0].graph), {'status': 'unavailable', 'reason': reason})
        value['observations'] = [{'kind': observation.kind, 'identity': json.loads(observation.identity), 'sha256': observation.sha256}]
        return cls(selection, encode(value), (observation,))

    @classmethod
    def from_result(cls, result):
        require((result.context is None) != (result.failure is None), 'campaign_graph_result_shape')
        if result.failure is not None:
            return cls.unavailable(result.selection, result.failure)
        try:
            return cls.bind(result.selection, result.context)
        except ValueError as error:
            if str(error) != 'campaign_graph_projection_limit':
                raise
            return cls.unavailable(result.selection, str(error))

    @classmethod
    def bind(cls, selection, supplied):
        selection = CampaignGraphSelection.bind(selection.request, *selection.parts())
        pins, entity_refs, assertion_refs = selection.parts()
        context = PinnedGraphContext.bind(pins, supplied.profile(), supplied.snapshot())
        facts, snapshot = context.index(), context.snapshot()
        require(all(ref in facts.entities for ref in entity_refs), 'campaign_graph_projection_entity')
        require(all(ref in facts.assertions for ref in assertion_refs), 'campaign_graph_projection_assertion')
        selected, present = list(entity_refs), set(entity_refs)

        def include(ref):
            if ref not in present:
                present.add(ref)
                selected.append(ref)

        assertions = [facts.assertions[ref] for ref in assertion_refs]
        for assertion in assertions:
            include(assertion.subject)
            include(assertion.object)
        aliases = {} if snapshot is None else {row.source.entity_id: row for row in snapshot.content.aliases}
        retractions = {} if snapshot is None else {row.assertion: row for row in snapshot.content.retractions}
        relevant_aliases = {}
        # Iteration grows only through bounded, already cycle-checked owner records.
        for ref in selected:
            alias = aliases.get(ref.entity_id)
            relevant_aliases[ref.entity_id] = alias
            if alias is not None:
                include(alias.source)
                include(alias.target)
        entities = [facts.entities[ref] for ref in sorted(selected, key=lambda ref: (ref.entity_id, ref.revision))]
        observations = [GraphObservation.capture('availability', wire(pins.graph), {'status': 'available'}),
                        GraphObservation.capture('profile', wire(pins.graph), wire(context.profile()))]
        observations.extend(GraphObservation.capture('entity', wire(row.reference), wire(row)) for row in entities)
        observations.extend(GraphObservation.capture('assertion', wire(row.reference), wire(row)) for row in assertions)
        for key, alias in sorted(relevant_aliases.items()):
            observations.append(GraphObservation.capture('alias', {'graph': wire(pins.graph), 'entity_id': key},
                None if alias is None else wire(alias)))
        for ref in assertion_refs:
            row = retractions.get(ref)
            observations.append(GraphObservation.capture('retraction', wire(ref), None if row is None else wire(row)))
        value = {'format': 'planning-campaign-graph-context.v1', 'authority': 'selected_metadata_only', 'status': 'available',
            'request_sha256': selection.request.sha256, 'selection_sha256': selection.sha256,
            'selection': json.loads(selection.canonical), 'profile': wire(context.profile()),
            'context_sha256': hashlib.sha256(context.profile_bytes + b'\n' + (context.snapshot_bytes or b'')).hexdigest(),
            'entities': [wire(row) for row in entities], 'assertions': [wire(row) for row in assertions],
            'aliases': [wire(row) for _, row in sorted(relevant_aliases.items()) if row is not None],
            'retractions': [wire(retractions[ref]) for ref in assertion_refs if ref in retractions],
            'observations': [{'kind': row.kind, 'identity': json.loads(row.identity), 'sha256': row.sha256} for row in observations]}
        raw = encode(value)
        require(len(raw) <= 1048576, 'campaign_graph_projection_limit')
        return cls(selection, raw, tuple(observations))

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def changes(self, observed):
        require(self.selection.request.document().reference.scope == observed.selection.request.document().reference.scope,
                'campaign_graph_comparison_scope')
        current = {(row.kind, row.identity): row.sha256 for row in observed.observations}
        return tuple(row for row in self.observations if current.get((row.kind, row.identity)) != row.sha256)
