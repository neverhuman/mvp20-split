"""Pure request-bound campaign candidates; no dispatch or execution authority."""

from .candidate import CampaignCandidate
from .decision import CampaignDecisionScope
from .output import CampaignOutput

__all__ = ['CampaignCandidate', 'CampaignDecisionScope', 'CampaignOutput']
