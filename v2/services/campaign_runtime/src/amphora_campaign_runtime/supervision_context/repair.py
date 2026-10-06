"""Only owned immutable report/disposition evidence enters a repair declaration."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_supervision import CheckpointRepairFeedback
from sqlalchemy import text

from ..supervision_outcomes.reports import KEY, ReportJournal
from ..supervision_requests.binding import encoded
from ..supervision_resolution.disposition import RequestDisposition
from ..supervision_resolution.resolver import OutcomeResolver
from ..supervision_scope.observations import require


@dataclass(frozen=True)
class RepairEvidence:
    canonical: bytes

    def __post_init__(self):
        require(type(self.canonical) is bytes and encoded(self.document()) == self.canonical,
                'noncanonical_repair_feedback')

    def document(self):
        return CheckpointRepairFeedback.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def require_parent(self, previous):
        require(bool(previous) and self.document().parent_request_sha256 == previous[-1].request_sha256,
                'repair_feedback_parent')

    @classmethod
    def load(cls, conn, params, parent):
        if parent is None:
            return None
        params = {**params, 'request': parent}
        row = conn.execute(text('SELECT * FROM runtime.supervision_request_dispositions WHERE ' + KEY),
                           params).mappings().one_or_none()
        if row is None:
            return None
        original = ReportJournal.source(conn, params)
        saved = ReportJournal.load(conn, params, original)
        require(saved is not None, 'repair_feedback_report_missing')
        responses = OutcomeResolver.responses(conn, params)
        disposition = RequestDisposition.restore(row, saved.report, responses)
        value = disposition.document()
        require(value.kind == 'repair', 'repair_feedback_disposition')
        response = next((item.bound.document() for item in responses if
                         item.bound.document().response_id == value.response_id), None)
        document = CheckpointRepairFeedback(parent_request_sha256=value.request_sha256,
            execution_report_sha256=value.report_sha256, disposition_sha256=disposition.sha256,
            response_sha256=value.response_sha256, reason_code=value.reason_code,
            observation_reason_code=None if response is None else response.observation.reason_code)
        return cls(encoded(document))
