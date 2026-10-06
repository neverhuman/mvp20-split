"""Reconstruct existing owned records inside the caller's read-only transaction."""

from sqlalchemy import text

from ..graph_inspection.policy import require
from ..supervision_journal.responses import RESPONSES, StoredResponse
from ..supervision_journal.storage import SELECT, StoredRequest
from ..supervision_outcomes.reports import KEY, ReportJournal
from ..supervision_resolution.disposition import RequestDisposition


def original_request(conn, params):
    row = conn.execute(text(SELECT + ' AND r.request_sha256=:request'), params).mappings().one_or_none()
    require(row is not None, 'supervision_request_unavailable')
    return StoredRequest.from_row(row)


def disposition(conn, params, report):
    row = conn.execute(text('SELECT * FROM runtime.supervision_request_dispositions WHERE ' + KEY),
                       params).mappings().one_or_none()
    if row is None:
        return None
    require(report is not None, 'supervision_report_unavailable')
    record = RequestDisposition(bytes(row['canonical_bytes'])).document()
    responses = []
    if record.response_id is not None:
        response = conn.execute(text(RESPONSES + ' AND s.run_id=:run AND s.decision_id=:decision '
            'AND s.request_sha256=:request AND s.response_id=:response'),
            {**params, 'response': record.response_id}).mappings().one_or_none()
        require(response is not None, 'supervision_response_unavailable')
        responses.append(StoredResponse.from_row(response))
    return RequestDisposition.restore(row, report.report, responses)


def request_details(conn, params, original):
    report = ReportJournal.load(conn, params, original)
    return report, disposition(conn, params, report)
