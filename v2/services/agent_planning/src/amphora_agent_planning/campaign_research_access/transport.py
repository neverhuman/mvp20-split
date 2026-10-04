"""Compiled selected-record reads; defaults for extraction readers remain unchanged."""

from amphora_contracts_research import (
    EvidenceAssessmentRequest,
    EvidenceAssessmentStatus,
    EvidenceNeed,
    EvidenceNeedRef,
    ResearchQuestion,
    ResearchQuestionRef,
)

from ..peer_reads.profile import ReadProfile, ReadWindow
from ..peer_reads.transport import BoundedReadTransport

PROFILE = ReadProfile("research", 20, 160, 4194304, {
    "/v1/questions/read": (ResearchQuestionRef, ResearchQuestion, 1048576),
    "/v1/evidence-needs/read": (EvidenceNeedRef, EvidenceNeed, 1048576),
    "/v1/assessments/read": (EvidenceAssessmentRequest, EvidenceAssessmentStatus, 1048576),
}, request_bytes=262144)


class CampaignResearchWindow(ReadWindow):
    def __init__(self, seconds=20):
        super().__init__(PROFILE, seconds)


class CampaignResearchTransport(BoundedReadTransport):
    def __init__(self, endpoint, token):
        super().__init__(endpoint, token, PROFILE)
