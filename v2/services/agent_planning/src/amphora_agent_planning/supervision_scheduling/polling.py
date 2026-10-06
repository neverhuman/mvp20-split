"""Fair execution/publication turns, separate from HTTP intake and model authority."""

import time
from dataclasses import dataclass

from amphora_contracts_planning import EngagementRef, ProviderAttemptRef
from amphora_tool_protocol import CommandUnresolved, TransportLost

from ..context.policy import require
from ..supervision_client import ExchangeUnavailable
from .discovery import WorkDiscovery


@dataclass(frozen=True)
class PlanningStep:
    stage: str
    engagement_id: str
    reason: str | None = None


class PlanningCheckpointPoller:
    def __init__(self, engine, worker, publisher, responder):
        self.discovery = WorkDiscovery(engine)
        self.worker, self.publisher, self.responder = worker, publisher, responder
        self.turns = {}

    def tick(self, principal):
        for action in ('record_requests', 'read_attempts', 'record_attempts'):
            principal.require(action, principal.scope)
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
        first = self.turns.get(key, 'execution')
        second = 'capture' if first == 'execution' else 'execution'
        for lane in (first, second):
            row = self.discovery.next(principal, lane)
            if row is None:
                continue
            self.turns[key] = 'capture' if lane == 'execution' else 'execution'
            if lane == 'execution':
                result = self.worker.run(principal, row.engagement_id)
                return PlanningStep('execution', row.engagement_id, result.stop_reason)
            return self._capture(principal, row)
        return None

    def _capture(self, principal, row):
        reference = EngagementRef(scope=principal.scope, engagement_id=row.engagement_id)
        attempt = ProviderAttemptRef(engagement=reference, ordinal=row.ordinal,
            request_sha256=self.worker.intake.request(principal, row.engagement_id).planning.sha256)
        try:
            state = self.publisher.publish(principal, attempt, kind=row.kind)
            if state.attempt is not None and state.attempt.stage == 'rejected':
                return PlanningStep('capture_rejected', row.engagement_id)
            result = self.responder.send(principal, state.identity.publication_id)
            return PlanningStep('capture_response', row.engagement_id,
                                None if result.observation is None else result.observation.status)
        except (CommandUnresolved, TransportLost, ExchangeUnavailable):
            return PlanningStep('capture_pending', row.engagement_id, 'peer_uncertain')
        except ValueError as error:
            if str(error) not in {'capture_lease_unavailable', 'capture_lease_lost', 'capture_event_limit',
                                  'publication_event_limit',
                                  'publication_attempt_limit', 'capture_response_limit'}:
                raise
            return PlanningStep('capture_pending', row.engagement_id, str(error))

    def sweep(self, principal, *, seconds=20, interval=1):
        require(type(seconds) in (int, float) and 0 < seconds <= 86400 and
                type(interval) in (int, float) and 0.05 <= interval <= 60, 'checkpoint_polling_window')
        deadline, counts = time.monotonic() + seconds, {}
        while time.monotonic() < deadline:
            result = self.tick(principal)
            stage = 'idle' if result is None else result.stage
            counts[stage] = counts.get(stage, 0) + 1
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(interval, remaining))
        return counts
