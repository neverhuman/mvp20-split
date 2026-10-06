"""One authenticated read outside SQL, then immutable original-report persistence."""

from ..supervision_client import ExchangeWindow
from ..supervision_journal.storage import outgoing
from ..supervision_scope.observations import require


class ReportCollector:
    def __init__(self, journal, client):
        self.journal, self.client = journal, client

    def run(self, principal, reference, request_sha256):
        previous = self.journal.read(principal, reference, request_sha256)
        if previous is not None:
            return previous
        principal.require('supervise_dispatch')
        params = self.journal.params(principal, reference, request_sha256)
        with self.journal.requests.engine.connect() as conn:
            original = self.journal.source(conn, params)
        require(original.frame.document().prepared_by == principal.actor_id, 'execution_report_observer')
        command = outgoing(original.frame, original.canonical_command)
        require(self.client is not None and self.client.actor_id == command.identity.actor_id and
                self.client.scope == command.identity.scope and self.client.family == command.identity.command_family,
                'execution_report_client')
        report = self.client.execution(command, ExchangeWindow())
        return self.journal.record(principal, reference, request_sha256, report)
