"""Exact Research selections for campaign context; no read or scientific authority."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, WireModel
from amphora_contracts_research import (
    EvidenceAssessmentRequest,
    EvidenceNeedRef,
    ResearchQuestionRef,
)
from pydantic import Field

from .engagement import EngagementRef


class CampaignAssessmentSelection(WireModel):
    request: EvidenceAssessmentRequest
    status_sha256: Digest


class CampaignResearchSelection(WireModel):
    schema_version: Literal["1"] = "1"
    engagement: EngagementRef
    request_sha256: Digest
    questions: Annotated[tuple[ResearchQuestionRef, ...], Field(max_length=64)]
    needs: Annotated[tuple[EvidenceNeedRef, ...], Field(max_length=64)]
    assessments: Annotated[tuple[CampaignAssessmentSelection, ...], Field(max_length=32)]
