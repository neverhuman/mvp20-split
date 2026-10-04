"""Independent selected records survive peer gaps; only exact values enter context."""

from dataclasses import dataclass

from pydantic import ValidationError

from ..campaign_context import (
    ResearchContext,
    ResearchGap,
    ResearchIdentity,
    ResearchSelection,
)
from ..campaign_context.records import ResearchRecord
from ..context.policy import require
from .transport import PROFILE, CampaignResearchWindow

PEER_CODES = frozenset({"research_access_denied", "research_reference_unavailable", "research_peer_unavailable",
    "research_peer_protocol", "research_peer_media", "research_response_limit", "research_request_size",
    "research_read_expired", "research_read_byte_limit", "research_read_call_limit"})
STOP_CODES = frozenset({"research_peer_unavailable", "research_read_expired", "research_read_byte_limit", "research_read_call_limit"})
RECORD_CODES = frozenset({"campaign_record_size", "campaign_record_not_selected", "campaign_record_duplicate",
    "campaign_assessment_digest", "campaign_context_record_bytes", "campaign_record_scope",
    "campaign_record_duplicate_criterion", "campaign_record_predecessor", "campaign_record_unknown_criterion",
    "campaign_assessment_request", "campaign_assessment_origin", "campaign_assessment_duplicate_need",
    "campaign_assessment_need_binding", "campaign_assessment_gap_binding", "campaign_assessment_receipt_binding"})


def failure_code(error):
    if isinstance(error, ValidationError):
        return "research_record_invalid"
    code = str(error)
    if code in PEER_CODES:
        return code
    if code in RECORD_CODES:
        return "research_record_binding" if code in {"campaign_record_not_selected", "campaign_assessment_digest"} else "research_record_invalid"
    raise error


@dataclass(frozen=True)
class ResearchReadFailure:
    identity: ResearchIdentity
    code: str


@dataclass(frozen=True)
class ResearchReadReport:
    context: ResearchContext
    failures: tuple[ResearchReadFailure, ...]
    calls: int
    bytes: int


class ResearchRecordReader:
    def __init__(self, transport):
        self.transport = transport

    def review(self, selection, window=None):
        selection = ResearchSelection.from_bytes(selection.canonical, selection.request)
        window = CampaignResearchWindow() if window is None else window
        require(window.profile == PROFILE, "research_read_profile_mismatch")
        start_calls, start_bytes = window.calls, window.consumed
        chosen = selection.document()
        records = {"questions": (), "needs": (), "assessments": ()}
        unavailable, failures, stopped = [], [], None
        for kind, field, path, references in (
            ("question", "questions", "/v1/questions/read", chosen.questions),
            ("need", "needs", "/v1/evidence-needs/read", chosen.needs),
            ("assessment", "assessments", "/v1/assessments/read", tuple(item.request for item in chosen.assessments)),
        ):
            for reference in references:
                identity = ResearchIdentity.bind(kind, reference)
                reason = stopped
                if reason is None:
                    try:
                        response = self.transport.read(path, reference, window)
                        require(ResearchRecord.bind(kind, response).identity == identity, "campaign_record_not_selected")
                        trial = {**records, field: (*records[field], response)}
                        ResearchContext.bind(selection, **trial, unavailable=tuple(unavailable))
                        window.remaining()
                    except ValueError as error:
                        reason = failure_code(error)
                        if reason in STOP_CODES:
                            stopped = reason
                    else:
                        records = trial
                        continue
                unavailable.append(ResearchGap(identity, "denied" if reason == "research_access_denied" else "unavailable"))
                failures.append(ResearchReadFailure(identity, reason))
        context = ResearchContext.bind(selection, **records, unavailable=tuple(unavailable))
        return ResearchReadReport(context, tuple(failures), window.calls - start_calls, window.consumed - start_bytes)
