"""Actual Runtime owners and an explicitly scripted public Planning boundary."""

import hashlib
import json

from amphora_campaign_runtime.supervision_client import ExchangeAbsent
from amphora_campaign_runtime.supervision_delivery import RequestDispatcher
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_campaign_runtime.supervision_loop import CheckpointLoop
from amphora_campaign_runtime.supervision_outcomes.collection import ReportCollector
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_responses import SupervisionReceiptObservation
from amphora_contracts_supervision import CheckpointRequest, SupervisionCommandReceipt

from ..supervision_outcomes.test_reported import bind, report
from ..supervision_resolution.support import setup


def request(command):
    return CheckpointRequest.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))


class Planning:
    family = 'planning.supervision.request.v2'
    actor_id = 'fixture'

    def __init__(self, scope):
        self.scope, self.saved, self.calls = scope, set(), []
        self.rejected, self.report_error = False, None

    def receipt(self, command, window, previous=None):
        self.calls.append('receipt')
        if command.sha256 not in self.saved:
            raise ExchangeAbsent('fixture_absent')
        outcome = {'status': 'rejected' if self.rejected else 'recorded', 'binding': {
            'identity': command.identity, 'request_sha256': command.sha256, 'operation_id': 'fixture-operation'}}
        if self.rejected:
            outcome['reason_code'] = 'fixture_rejected'
        else:
            outcome['committed'] = {'kind': 'request', 'object_id': request(command).planning_request.reference.engagement_id,
                'revision': 1, 'content_sha256': hashlib.sha256(encoded(request(command))).hexdigest()}
        value = SupervisionCommandReceipt.model_validate({'outcome': outcome})
        return SupervisionReceiptObservation.observe(command, value, previous=previous)

    def submit(self, command, window, guard):
        guard()
        self.calls.append('submit')
        self.saved.add(command.sha256)
        return self.receipt(command, window)

    def readback(self, command, previous, window):
        self.calls.append('readback')
        return SupervisionReceiptObservation.observe(command, previous.document(), readback=request(command),
                                                      previous=previous)

    def execution(self, command, window):
        self.calls.append('execution')
        if self.report_error is not None:
            raise self.report_error
        return bind(report(request(command)), request(command))


def fixture(graph, *, prepare=False):
    actor, ref, slot, preparer, original, resolver = setup(graph, prepare=prepare)
    peer = Planning(actor.scope)
    dispatcher = RequestDispatcher(DeliveryJournal(preparer.journal), peer)
    collector = ReportCollector(resolver.reports, peer)
    loop = CheckpointLoop(preparer, dispatcher, collector, resolver)
    return actor, ref, slot, loop, peer, original
