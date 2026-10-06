"""Original Planning request submission and exact recording receipt/readback."""

import json
from urllib.parse import quote

from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionCommandReceipt,
    SupervisionRequest,
)

from ..supervision_requests.profiles import request_command
from ..supervision_responses import SupervisionReceiptObservation
from ..supervision_scope.observations import require
from .transport import SupervisorTransport


class PlanningClient(SupervisorTransport):
    family = 'planning.supervision.request'
    prefix = '/v1/supervision'
    request_type = SupervisionRequest

    def _command(self, command):
        require(request_command(self.family, command.canonical_bytes) == command,
                'supervisor_command_mismatch')
        require(command.identity.actor_id == self.actor_id and command.identity.scope == self.scope,
                'supervisor_client_authority')
        return command

    def submit(self, command, window, *, guard):
        checked = self._command(command)
        receipt = self._exchange('POST', self.prefix + '/requests', checked.canonical_bytes,
                                SupervisionCommandReceipt, window, write=True, guard=guard)
        return SupervisionReceiptObservation.observe(checked, receipt)

    def receipt(self, command, window, *, previous=None):
        checked = self._command(command)
        receipt = self._exchange('POST', self.prefix + '/receipts/query', checked.canonical_bytes,
                                SupervisionCommandReceipt, window)
        return SupervisionReceiptObservation.observe(checked, receipt, previous=previous)

    def readback(self, command, observation, window):
        checked = self._command(command)
        verified = SupervisionReceiptObservation.observe(checked, observation.document(), previous=observation)
        require(verified == observation and observation.document().outcome.status == 'recorded', 'supervisor_recorded_required')
        payload = self.request_type.model_validate_json(json.dumps(json.loads(checked.canonical_bytes)['payload']))
        value = self._exchange('GET', self.prefix + '/requests/' + quote(payload.planning_request.reference.engagement_id, safe=''),
                               None, self.request_type, window)
        return SupervisionReceiptObservation.observe(checked, observation.document(), readback=value, previous=observation)


class CheckpointPlanningClient(PlanningClient):
    family = 'planning.supervision.request.v2'
    prefix = '/v2/supervision'
    request_type = CheckpointRequest
