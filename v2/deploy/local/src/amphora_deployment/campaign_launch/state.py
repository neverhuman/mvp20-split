"""Launch lifecycle invariants; peer observations cannot rewrite committed identity."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone

from amphora_contracts_campaign_launch import LaunchReceipt, WorkerReadiness
from amphora_contracts_runtime import CommandReceipt

from .intent import LaunchError, LaunchIntent

TRANSITIONS = {
    'preparing': {'admission_unresolved', 'rejected', 'recovery_required'},
    'admission_unresolved': {'admitted_not_engaged', 'rejected', 'recovery_required'},
    'admitted_not_engaged': {'engaging', 'draining', 'recovery_required'},
    'engaging': {'engaged', 'admitted_not_engaged', 'draining', 'recovery_required'},
    'engaged': {'admitted_not_engaged', 'draining', 'recovery_required'},
    'draining': {'released', 'recovery_required'},
    'recovery_required': {'admitted_not_engaged'}, 'rejected': set(), 'released': set(),
}


@dataclass(frozen=True, slots=True)
class LaunchState:
    intent: LaunchIntent
    revision: int
    phase: str
    reason: str | None
    created: datetime
    updated: datetime
    admission: CommandReceipt | None = None
    expected_workers: int = 0
    ready_workers: int = 0

    @classmethod
    def initial(cls, intent: LaunchIntent, now: datetime):
        if now.tzinfo is None:
            raise LaunchError('launch_clock_invalid')
        return cls(intent, 0, 'preparing', None, now, now)

    @property
    def run_id(self):
        outcome = self.admission.outcome if self.admission else None
        return outcome.committed.object_id if outcome and outcome.status == 'accepted' else None

    @property
    def terminal(self):
        return self.phase in {'rejected', 'released'}

    def _changed(self, now: datetime, **changes):
        if now.tzinfo is None or now < self.updated:
            raise LaunchError('launch_clock_invalid')
        return replace(self, revision=self.revision + 1, updated=now, **changes)

    def move(self, phase: str, now: datetime, reason: str | None = None):
        if phase not in TRANSITIONS.get(self.phase, set()):
            raise LaunchError('launch_transition_invalid')
        if phase in {'admitted_not_engaged', 'engaging', 'engaged', 'draining', 'released'} and not self.run_id:
            raise LaunchError('launch_admission_required')
        if phase == 'rejected' and self.run_id:
            raise LaunchError('launch_cannot_reject_admitted')
        if phase == 'engaged' and (self.expected_workers == 0 or self.ready_workers != self.expected_workers):
            raise LaunchError('launch_workers_not_ready')
        return self._changed(now, phase=phase, reason=reason)

    def observe_admission(self, receipt: CommandReceipt, now: datetime):
        outcome = receipt.outcome
        if outcome.binding.identity != self.intent.admission.identity or outcome.binding.request_sha256 != self.intent.admission.sha256:
            raise LaunchError('launch_admission_binding')
        if self.admission:
            prior = self.admission.outcome
            if prior.binding.operation_id != outcome.binding.operation_id:
                raise LaunchError('launch_admission_binding')
            if prior.status != 'pending':
                if self.admission != receipt:
                    raise LaunchError('launch_admission_changed')
                return self
        if self.phase != 'admission_unresolved':
            raise LaunchError('launch_admission_intent_required')
        if outcome.status == 'accepted':
            if outcome.committed.kind != 'run' or outcome.committed.revision != 0:
                raise LaunchError('launch_admission_binding')
            return self._changed(now, phase='admitted_not_engaged', admission=receipt, reason=None)
        if outcome.status == 'rejected':
            return self._changed(now, phase='rejected', admission=receipt, reason=outcome.reason_code)
        return self._changed(now, admission=receipt, reason='admission_pending')

    def readiness(self, expected: int, ready: int, now: datetime):
        if self.phase not in {'admitted_not_engaged', 'engaging', 'engaged', 'draining'} or type(expected) is not int or type(ready) is not int or not 0 <= ready <= expected <= 64:
            raise LaunchError('launch_readiness_invalid')
        return self._changed(now, expected_workers=expected, ready_workers=ready)

    def note(self, reason: str, now: datetime):
        if self.terminal:
            raise LaunchError('launch_transition_invalid')
        return self if self.reason == reason else self._changed(now, reason=reason)

    def worker_observation(self, observation, now: datetime, *, phase=None, reason=None):
        """Apply one worker observation as one journal revision, including its phase."""
        if (observation.expected == self.expected_workers and observation.ready == self.ready_workers
                and (phase is None or phase == self.phase) and reason == self.reason):
            return self
        updated = self.readiness(observation.expected, observation.ready, now)
        if phase is not None and phase != self.phase:
            updated = updated.move(phase, now, reason)
        return replace(updated, revision=self.revision + 1, reason=reason)

    def receipt(self) -> LaunchReceipt:
        return LaunchReceipt(identity=self.intent.request.identity, request_sha256=self.intent.request.sha256,
            profile=self.intent.profile, revision=self.revision, phase=self.phase, reason_code=self.reason,
            created_at=self.created, updated_at=self.updated, admission=self.admission, run_id=self.run_id,
            workers=WorkerReadiness(expected=self.expected_workers, ready=self.ready_workers))

    @classmethod
    def restore(cls, intent: LaunchIntent, raw: bytes):
        try:
            record = LaunchReceipt.model_validate_json(raw)
            state = cls(intent, record.revision, record.phase, record.reason_code,
                record.created_at, record.updated_at, record.admission, record.workers.expected, record.workers.ready)
            if state.receipt() != record or state.created > state.updated or state.ready_workers > state.expected_workers:
                raise ValueError()
            if record.admission:
                outcome = record.admission.outcome
                binding = outcome.binding
                if binding.identity != intent.admission.identity or binding.request_sha256 != intent.admission.sha256:
                    raise ValueError()
                if outcome.status == 'accepted' and (outcome.committed.kind != 'run' or outcome.committed.revision != 0):
                    raise ValueError()
                if state.phase == 'preparing' or (outcome.status == 'pending' and state.phase not in {'admission_unresolved', 'recovery_required'}):
                    raise ValueError()
                if outcome.status == 'rejected' and state.phase != 'rejected':
                    raise ValueError()
                if outcome.status == 'accepted' and state.phase == 'admission_unresolved':
                    raise ValueError()
            if state.phase in {'admitted_not_engaged', 'engaging', 'engaged', 'draining', 'released'} and not state.run_id:
                raise ValueError()
            if state.phase == 'rejected' and state.run_id:
                raise ValueError()
            if state.phase == 'engaged' and (not state.expected_workers or state.ready_workers != state.expected_workers):
                raise ValueError()
            return state
        except ValueError:
            raise LaunchError('launch_journal_corrupt') from None


def utc_now():
    return datetime.now(timezone.utc)
