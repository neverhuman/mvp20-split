"""Campaign context projection of selected Research records and named pages."""

from .projection import CampaignResearchProjection, ResearchObservation
from .views import CampaignViewContext

__all__ = ['CampaignResearchProjection', 'CampaignViewContext', 'ResearchObservation']
