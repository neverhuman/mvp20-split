"""Bounded exact Research reads for campaign context; no declaration writes."""

from .reader import ResearchReadReport, ResearchRecordReader
from .transport import CampaignResearchTransport, CampaignResearchWindow

__all__ = ["CampaignResearchTransport", "CampaignResearchWindow", "ResearchReadReport", "ResearchRecordReader"]
