"""Recover durable receipts before performing new capture processing."""

import json

from amphora_contracts_supervision import (
    SupervisionRef,
    SupervisionResponse,
    parse_supervision_command,
)
from sqlalchemy import text

from ..supervision_capture import CaptureUnavailable
from ..supervision_journal.cancellations import CancellationJournal
from ..supervision_journal.responses import ResponseJournal
from ..supervision_scope.observations import require
from ..supervision_winners.storage import WinnerStore


class SupervisorRecording:
    def __init__(self, requests, captures=None):
        self.requests, self.captures = requests, captures
        self.responses = ResponseJournal(requests)
        self.cancellations = CancellationJournal(requests)

    def ready(self):
        with self.requests.engine.connect() as conn:
            conn.execute(text('SELECT canonical_frame FROM runtime.supervision_requests LIMIT 0'))
            conn.execute(text('SELECT canonical_response FROM runtime.supervision_responses LIMIT 0'))
            conn.execute(text('SELECT canonical_cancellation FROM runtime.supervision_cancellations LIMIT 0'))
        return {'status': 'ready', 'mode': 'supervisor_recording_only'}

    def respond(self, principal, raw):
        command = parse_supervision_command('runtime.supervision.respond', raw)
        principal.require('supervise_respond', command.identity)
        receipt = self.responses.receipt(principal, command)
        if receipt is not None:
            return receipt
        response = SupervisionResponse.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
        matches = [item.frame for item in self.requests.series(principal, response.reference.run_id,
                   response.reference.decision_id) if item.frame.request_sha256 == response.request_sha256]
        require(len(matches) == 1, 'supervision_request_unavailable')
        original = matches[0].request
        require(original.planning_request.actor_id == principal.actor_id, 'response_actor_mismatch')
        require(response.reference == original.reference, 'response_request_mismatch')
        require(response.observation.attempt.engagement == original.planning_request.reference and
                response.observation.attempt.request_sha256 == original.planning_request_sha256,
                'response_attempt_mismatch')
        require(response.capture is None or response.capture.scope == principal.scope, 'capture_scope_mismatch')
        if response.capture is not None and self.captures is None:
            raise CaptureUnavailable('capture_reader_unavailable')
        capture = None if response.capture is None else self.captures.fetch(response.capture)
        return self.responses.record(principal, command, capture_bytes=capture)

    def cancel(self, principal, raw):
        return self.cancellations.record(principal, parse_supervision_command('runtime.supervision.cancel', raw))

    def receipt(self, principal, family, raw):
        command = parse_supervision_command(family, raw)
        owner = self.responses if family == 'runtime.supervision.respond' else self.cancellations
        return owner.receipt(principal, command)

    def response(self, principal, response_id):
        result = self.responses.response(principal, response_id)
        return None if result is None else result.bound.document()

    def cancellation(self, principal, cancellation_id):
        result = self.cancellations.cancellation(principal, cancellation_id)
        return None if result is None else result.bound.document()

    def decision(self, principal, run_id, decision_id):
        reference = SupervisionRef(scope=principal.scope, run_id=run_id, decision_id=decision_id)
        result = WinnerStore(self.requests.engine).read(principal, reference)
        return None if result is None else result.document()
