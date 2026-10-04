"""Fresh per-operation processing reads; retained payloads never renew rights."""

from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from pydantic import ValidationError

from ..context.policy import require
from ..source_access.artifacts import ArtifactReview
from ..source_access.budget import ReadBudget
from .selection import ArtifactSelection

CODES = frozenset({"source_access_denied", "source_reference_unavailable", "source_peer_unavailable", "source_peer_protocol",
    "source_peer_response_limit", "source_review_deadline", "source_review_call_limit", "source_review_byte_limit",
    "source_artifact_scope", "source_artifact_conflict", "source_input_count", "source_artifact_size",
    "source_artifact_binding", "source_artifact_bytes"})
STOP_CODES = frozenset({"source_peer_unavailable", "source_review_deadline", "source_review_call_limit", "source_review_byte_limit"})


@dataclass(frozen=True)
class ArtifactBody:
    reference: ArtifactRef
    body: bytes


@dataclass(frozen=True)
class ArtifactFailure:
    reference: ArtifactRef
    code: str


@dataclass(frozen=True)
class ArtifactReadResult:
    selection: ArtifactSelection
    records: tuple[ArtifactBody, ...]
    failures: tuple[ArtifactFailure, ...]
    calls: int
    bytes: int


class CampaignArtifactReader:
    def __init__(self, data):
        self.data = data

    def read(self, selection, budget=None):
        selection = ArtifactSelection.bind(selection.request, selection.references())
        budget = ReadBudget() if budget is None else budget
        require(isinstance(budget, ReadBudget), "campaign_artifact_budget")
        calls, consumed = budget.calls, budget.consumed
        review = ArtifactReview(self.data, selection.request.document().reference.scope, budget)
        records, failures, stopped = [], [], None
        for ref in selection.references():
            code = stopped
            if code is None:
                try:
                    body = review.artifact(ref)
                    budget.remaining_total()
                except ValueError as error:
                    if isinstance(error, ValidationError):
                        code = "campaign_artifact_invalid"
                    elif str(error) in CODES:
                        code = str(error)
                    else:
                        raise
                    if code in STOP_CODES:
                        stopped = code
                else:
                    records.append(ArtifactBody(ref, body))
                    continue
            failures.append(ArtifactFailure(ref, code))
        return ArtifactReadResult(selection, tuple(records), tuple(failures), budget.calls - calls, budget.consumed - consumed)
