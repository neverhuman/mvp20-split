"""One retained Data selection read; no query creation, reranking or hidden retry."""

from dataclasses import dataclass

from pydantic import ValidationError

from ..context.policy import require
from ..metadata_reads import MetadataWindow
from .record import RetrievalObservation
from .selection import RetrievalSelection

PEER_CODES = frozenset({"metadata_denied", "metadata_missing", "metadata_unavailable", "metadata_media", "metadata_response_limit",
    "metadata_protocol", "metadata_deadline", "metadata_call_limit", "metadata_byte_limit"})
RECORD_CODES = frozenset({"retrieval_context_type", "retrieval_context_identity", "retrieval_context_scope", "retrieval_context_span",
    "retrieval_context_size", "retrieval_context_binding_digest", "retrieval_context_policy", "retrieval_context_query_digest",
    "retrieval_context_top_k", "retrieval_context_profile", "retrieval_context_filter", "retrieval_context_duplicate_binding",
    "retrieval_context_order", "retrieval_context_result_digest"})


@dataclass(frozen=True)
class RetrievalReadResult:
    selection: RetrievalSelection
    record: RetrievalObservation | None
    failure: str | None
    calls: int
    bytes: int


class RetrievalReader:
    def __init__(self, data):
        self.data = data

    def read(self, selection, window=None):
        selection = RetrievalSelection.bind(selection.request, selection.document(), selection.result_sha256)
        window = MetadataWindow("data") if window is None else window
        require(window.owner == "data", "metadata_window")
        calls, consumed = window.calls, window.consumed
        record, failure = None, None
        try:
            response = self.data.read("/v1/retrieval/queries/" + selection.document().retrieval_id, window)
            candidate = RetrievalObservation.bind(selection, response)
            window.remaining()
            record = candidate
        except ValueError as error:
            if isinstance(error, ValidationError) or str(error) in RECORD_CODES:
                failure = "retrieval_context_invalid"
            elif str(error) in PEER_CODES:
                failure = str(error)
            else:
                raise
        return RetrievalReadResult(selection, record, failure, window.calls - calls, window.consumed - consumed)
