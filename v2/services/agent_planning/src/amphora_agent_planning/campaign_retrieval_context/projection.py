"""Revalidated retained selection, source/vector provenance and explicit gaps."""

import hashlib
import json
from dataclasses import dataclass

from ..campaign_context.records import canonical
from ..context.policy import require
from ..retrieval_access import RetrievalObservation, RetrievalSelection
from ..retrieval_access.reader import PEER_CODES


@dataclass(frozen=True)
class RetrievalContext:
    selection: RetrievalSelection
    canonical: bytes

    @classmethod
    def bind(cls, request, result):
        selection = RetrievalSelection.bind(result.selection.request, result.selection.document(), result.selection.result_sha256)
        require(selection.request == request, 'campaign_retrieval_request')
        require((result.record is None) != (result.failure is None), 'campaign_retrieval_shape')
        record = None
        if result.record is not None:
            require(result.record.selection == selection, 'campaign_retrieval_selection')
            record = RetrievalObservation.bind(selection, result.record.document())
        else:
            require(result.failure in PEER_CODES | {'retrieval_context_invalid'}, 'campaign_retrieval_failure')
        raw = canonical({'format': 'planning-campaign-retrieval-context.v1', 'authority': 'retained_selection_only',
            'request_sha256': request.sha256, 'selection_sha256': selection.sha256,
            'query': selection.document().model_dump(mode='json'), 'result_sha256': selection.result_sha256,
            'status': 'available' if record is not None else 'unavailable', 'reason': result.failure,
            'record': None if record is None else json.loads(record.canonical)})
        require(len(raw) <= 8388608, 'campaign_retrieval_projection_limit')
        return cls(selection, raw)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
