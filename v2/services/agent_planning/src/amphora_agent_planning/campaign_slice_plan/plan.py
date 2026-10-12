"""Original-request assembly through closed, revalidated owner adapters."""

import hashlib
import json
from dataclasses import dataclass, replace

from amphora_contracts_campaign_curation import campaign_curation_draft_schema

from ..campaign_artifact_context import ArtifactContextProjection
from ..campaign_context.records import canonical
from ..campaign_graph_context import CampaignGraphProjection
from ..campaign_research_context import CampaignResearchProjection
from ..campaign_retrieval_context import RetrievalContext
from ..campaign_tool_context import RegistryContext, RuntimeContext
from ..context import RequestSnapshot
from ..context.policy import require
from .slices import ContextSlice, ordered


def observation(kind, identity, value):
    return {'kind': kind, 'identity': identity, 'sha256': hashlib.sha256(canonical(value)).hexdigest()}


@dataclass(frozen=True)
class CampaignSlicePlan:
    request: RequestSnapshot
    slices: tuple[ContextSlice, ...]
    families: tuple[str, ...]
    missing_required: tuple[str, ...]

    @classmethod
    def from_artifacts(cls, supplied):
        artifacts = ArtifactContextProjection.bind(supplied.plan, supplied.items)
        rows = []
        for item in artifacts.items:
            identity = item.planned.reference.model_dump(mode='json')
            rows.append(ContextSlice._capture('artifact', identity, item.payload(), item.planned.required,
                (observation('artifact', identity, item.metadata()),)))
        missing = tuple(item.planned.reference.artifact_id for item in artifacts.missing_required)
        return cls(artifacts.plan.request, ordered(tuple(rows)), ('artifacts',), missing)

    def _add(self, family, request, rows):
        require(request == self.request, 'campaign_slice_request')
        require(family not in self.families, 'campaign_slice_family_duplicate')
        return replace(self, slices=ordered(self.slices + tuple(rows)), families=(*self.families, family))

    def with_research(self, context, views=()):
        projection = CampaignResearchProjection.bind(context, views)
        value = json.loads(projection.canonical)
        rows = [ContextSlice._capture('research', {'selection': projection.context.selection.sha256},
            {'format': 'planning-campaign-research-slice.v1', 'selection': json.loads(projection.context.selection.canonical),
             'context': value['research']}, True, tuple(row for row in value['observations'] if row['kind'] == 'record'))]
        for page in projection.views:
            rows.append(ContextSlice._capture('research_view', json.loads(page.identity), json.loads(page.canonical), False,
                ({'kind': 'view', 'identity': json.loads(page.identity), 'sha256': page.observation_sha256},)))
        return self._add('research', projection.context.selection.request, rows)

    def with_graph(self, result):
        projection = CampaignGraphProjection.from_result(result)
        value = json.loads(projection.canonical)
        row = ContextSlice._capture('graph', {'selection': projection.selection.sha256}, value, True, value['observations'])
        return self._add('graph', projection.selection.request, (row,))

    def with_curation(self, intent):
        from ..curation_context import CurationIntent
        verified = CurationIntent.from_payload(intent.request, json.loads(intent.canonical))
        row = ContextSlice._capture('curation', verified.identity, json.loads(verified.canonical), True)
        return self._add('curation', verified.request, (row,))

    def with_curation_knowledge(self, context):
        projections, summary = context.rows()
        require(context.intent.request == self.request, 'campaign_slice_request')
        require('graph' not in self.families, 'campaign_slice_family_duplicate')
        rows = [ContextSlice._capture('curation_knowledge', context.intent.identity, summary, True)]
        for projection in projections:
            value = json.loads(projection.canonical)
            rows.append(ContextSlice._capture('graph', {'selection': projection.selection.sha256},
                value, True, value['observations']))
        return self._add('graph', self.request, rows)

    def with_graphs(self, results):
        # Only the new curation profile admits a bounded collection. Legacy
        # with_graph and its canonical single-graph history remain unchanged.
        require(self.request.document().context.output_schema == campaign_curation_draft_schema(),
                'campaign_graph_collection_profile')
        require(type(results) is tuple and 1 <= len(results) <= 8, 'campaign_graph_collection_bound')
        projections = tuple(CampaignGraphProjection.from_result(result) for result in results)
        require(all(item.selection.request == self.request for item in projections), 'campaign_slice_request')
        graphs = tuple(item.selection.parts()[0].graph for item in projections)
        require(len(set(graphs)) == len(graphs), 'campaign_graph_collection_duplicate')
        rows = []
        for projection in projections:
            value = json.loads(projection.canonical)
            rows.append(ContextSlice._capture('graph', {'selection': projection.selection.sha256},
                value, True, value['observations']))
        return self._add('graph', self.request, rows)

    def with_registry(self, result, exact=()):
        projection = RegistryContext.bind(result, exact)
        value = json.loads(projection.canonical)
        metadata = {key: item for key, item in value.items() if key not in {'inventory', 'exact'}}
        # Scan diagnostics are required but are not a blanket read-set for every tool.
        rows = [ContextSlice._capture('registry_scan', value['query'], metadata, True)]
        for lane, required in (('inventory', False), ('exact', True)):
            for record in value[lane]:
                identity = record['lock']
                rows.append(ContextSlice._capture('registry_' + lane, identity, record, required,
                    (observation('registry_' + lane, identity, record),)))
        return self._add('registry', projection.request, rows)

    def with_runtime(self, result):
        return self._runtime(RuntimeContext.bind(result))

    def with_runtime_unavailable(self, reason):
        return self._runtime(RuntimeContext.unavailable(self.request, reason))

    def _runtime(self, projection):
        value = json.loads(projection.canonical)
        metadata = {key: item for key, item in value.items() if key != 'schemas'}
        identity = {'scope': self.request.document().reference.scope.model_dump(mode='json')}
        rows = [ContextSlice._capture('runtime', identity, metadata, True,
            (observation('runtime_universe', identity, metadata),))]
        for record in value.get('schemas', ()):
            identity = record['reference']
            rows.append(ContextSlice._capture('runtime_schema', identity, record, True,
                (observation('runtime_schema', identity, record),)))
        return self._add('runtime', projection.request, rows)

    def with_retrieval(self, result):
        projection = RetrievalContext.bind(self.request, result)
        value = json.loads(projection.canonical)
        identity = {'selection': projection.selection.sha256}
        row = ContextSlice._capture('retrieval', identity, value, False, (observation('retrieval', identity, value),))
        return self._add('retrieval', projection.selection.request, (row,))

    @property
    def canonical(self):
        return canonical({'format': 'planning-campaign-slice-plan.v1', 'request_sha256': self.request.sha256,
            'families': list(self.families), 'missing_required': list(self.missing_required),
            'original_omissions': [row.model_dump(mode='json') for row in self.request.document().context.omissions],
            'slices': [row.document() for row in self.slices], 'authority': 'preparation_only'})

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
