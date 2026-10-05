"""Selected scientific records and named views retain gaps, findings and origin."""

import hashlib
import json
from dataclasses import dataclass

from ..campaign_context import ResearchContext, ResearchSelection
from ..campaign_context.records import canonical
from ..context.policy import require
from .views import CampaignViewContext


@dataclass(frozen=True)
class ResearchObservation:
    kind: str
    identity: bytes
    sha256: str


@dataclass(frozen=True)
class CampaignResearchProjection:
    context: ResearchContext
    views: tuple[CampaignViewContext, ...]
    canonical: bytes
    observations: tuple[ResearchObservation, ...]

    @classmethod
    def bind(cls, supplied, views=()):
        selection = ResearchSelection.from_bytes(supplied.selection.canonical, supplied.selection.request)
        groups = {'question': [], 'need': [], 'assessment': []}
        for row in supplied.records:
            require(row.identity.kind in groups, 'campaign_research_record_kind')
            groups[row.identity.kind].append(row.document())
        context = ResearchContext.bind(selection, questions=tuple(groups['question']), needs=tuple(groups['need']),
            assessments=tuple(groups['assessment']), unavailable=supplied.gaps)
        require(type(views) is tuple and len(views) <= 32, 'campaign_research_view_count')
        pages = tuple(CampaignViewContext.bind(selection.request, result) for result in views)
        require(len({page.identity for page in pages}) == len(pages), 'campaign_research_duplicate_view')
        observations = tuple(ResearchObservation('record', canonical(row.identity.document()), row.observation_sha256)
            for row in context.read_set().entries) + tuple(ResearchObservation('view', page.identity, page.observation_sha256) for page in pages)
        value = {'format': 'planning-campaign-research-projection.v1', 'authority': 'selected_metadata_only',
            'request_sha256': selection.request.sha256, 'research': json.loads(context.canonical),
            'views': [json.loads(page.canonical) for page in pages],
            'observations': [{'kind': row.kind, 'identity': json.loads(row.identity), 'sha256': row.sha256} for row in observations]}
        raw = canonical(value)
        require(len(raw) <= 8388608, 'campaign_research_projection_limit')
        return cls(context, pages, raw, observations)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def changes(self, observed):
        require(self.context.selection.request.document().reference.scope == observed.context.selection.request.document().reference.scope,
                'campaign_research_comparison_scope')
        current = {(row.kind, row.identity): row.sha256 for row in observed.observations}
        return tuple(row for row in self.observations if current.get((row.kind, row.identity)) != row.sha256)
