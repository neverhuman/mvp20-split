"""Original Runtime response/cancellation submission and exact recording recovery."""

import json
from urllib.parse import quote

from amphora_contracts_supervision import (
    CancelSupervision,
    SupervisionCommandReceipt,
    SupervisionResponse,
    parse_supervision_command,
)

from ..context.policy import require
from .observations import RecordingObservation
from .transport import SupervisorTransport


class RuntimeClient(SupervisorTransport):
    def _command(self, command):
        family = command.identity.command_family
        require(family in {'runtime.supervision.respond', 'runtime.supervision.cancel'}, 'supervisor_runtime_family')
        require(parse_supervision_command(family, command.canonical_bytes) == command, 'supervisor_command_mismatch')
        require(command.identity.actor_id == self.actor_id and command.identity.scope == self.scope,
                'supervisor_client_authority')
        return command

    @staticmethod
    def _path(command):
        return '/v1/supervision/' + ('responses' if command.identity.command_family == 'runtime.supervision.respond' else 'cancellations')

    def submit(self, command, window, *, guard):
        checked = self._command(command)
        receipt = self._exchange('POST', self._path(checked), checked.canonical_bytes,
                                SupervisionCommandReceipt, window, write=True, guard=guard)
        return RecordingObservation.observe(checked, receipt)

    def receipt(self, command, window, *, previous=None):
        checked = self._command(command)
        receipt = self._exchange('POST', self._path(checked) + '/receipts/query', checked.canonical_bytes,
                                SupervisionCommandReceipt, window)
        return RecordingObservation.observe(checked, receipt, previous=previous)

    def readback(self, command, observation, window):
        checked = self._command(command)
        verified = RecordingObservation.observe(checked, observation.document(), previous=observation)
        require(verified == observation and observation.document().outcome.status == 'recorded', 'supervisor_recorded_required')
        model, field = ((SupervisionResponse, 'response_id') if checked.identity.command_family == 'runtime.supervision.respond'
                        else (CancelSupervision, 'cancellation_id'))
        payload = model.model_validate_json(json.dumps(json.loads(checked.canonical_bytes)['payload']))
        value = self._exchange('GET', self._path(checked) + '/' + quote(getattr(payload, field), safe=''), None, model, window)
        return RecordingObservation.observe(checked, observation.document(), readback=value, previous=observation)
