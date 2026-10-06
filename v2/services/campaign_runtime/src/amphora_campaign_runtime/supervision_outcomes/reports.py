"""Immutable scoped owner evidence; recording a report never selects a winner."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_supervision import CheckpointExecutionReport, SupervisionRef
from sqlalchemy import text

from ..supervision_journal.storage import SELECT, StoredRequest
from ..supervision_scope.observations import digest, require
from .reported import ReportedExecution

KEY = 'tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision AND request_sha256=:request'


@dataclass(frozen=True)
class StoredReport:
    report: ReportedExecution
    observed_by: str
    created_at: datetime

    @classmethod
    def from_row(cls, row, original):
        report = ReportedExecution.bind(original.frame.request,
            CheckpointExecutionReport.model_validate_json(bytes(row['canonical_bytes'])))
        require(report.canonical == bytes(row['canonical_bytes']) and report.sha256 == row['report_sha256'] and
                row['observed_by'] == original.frame.document().prepared_by, 'stored_execution_report_corrupt')
        return cls(report, row['observed_by'], row['created_at'])


class ReportJournal:
    def __init__(self, requests):
        self.requests = requests

    def params(self, principal, reference, request_sha256):
        reference = SupervisionRef.model_validate_json(reference.model_dump_json())
        require(reference.scope == principal.scope, 'execution_report_scope')
        return {**self.requests.params(principal, reference.run_id, reference.decision_id),
                'request': digest(request_sha256)}

    @staticmethod
    def source(conn, params):
        row = conn.execute(text(SELECT + ' AND r.request_sha256=:request'), params).mappings().one_or_none()
        require(row is not None, 'supervision_request_unavailable')
        return StoredRequest.from_row(row)

    @staticmethod
    def load(conn, params, original):
        row = conn.execute(text('SELECT * FROM runtime.supervision_execution_reports WHERE ' + KEY),
                           params).mappings().one_or_none()
        return None if row is None else StoredReport.from_row(row, original)

    def read(self, principal, reference, request_sha256):
        principal.require('read')
        params = self.params(principal, reference, request_sha256)
        with self.requests.engine.connect() as conn:
            return self.load(conn, params, self.source(conn, params))

    def record(self, principal, reference, request_sha256, report):
        principal.require('supervise_dispatch')
        params = self.params(principal, reference, request_sha256)
        def transaction(conn):
            self.requests.leases._run(conn, params)
            original = self.source(conn, params)
            require(original.frame.document().prepared_by == principal.actor_id, 'execution_report_observer')
            checked = ReportedExecution.bind(original.frame.request, report.document())
            require(checked.canonical == report.canonical, 'execution_report_noncanonical')
            previous = self.load(conn, params, original)
            if previous is not None:
                require(previous.report == checked, 'execution_report_conflict')
                return previous
            row = conn.execute(text('INSERT INTO runtime.supervision_execution_reports '
                '(tenant_id,project_id,run_id,decision_id,request_sha256,observed_by,report_sha256,canonical_bytes) '
                'VALUES (:tenant,:project,:run,:decision,:request,:actor,:digest,:canonical) RETURNING *'),
                {**params, 'actor': principal.actor_id, 'digest': checked.sha256,
                 'canonical': checked.canonical}).mappings().one()
            return StoredReport.from_row(row, original)
        return self.requests.leases.commands.transact(transaction)
