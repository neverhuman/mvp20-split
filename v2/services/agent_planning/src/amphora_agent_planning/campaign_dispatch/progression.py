"""Lease-owned bounded compiler progression; no campaign activation or retry loop."""

from dataclasses import dataclass

from ..context.policy import require
from .dispatcher import CompilerFenceLost, DispatchStep
from .records import CompilerRound


@dataclass(frozen=True)
class CompilerAdvance:
    selection_id: str
    stage: str
    dispatch: DispatchStep | None = None
    round: CompilerRound | None = None
    pause_reason: str | None = None

    @property
    def terminal(self):
        if self.dispatch is None:
            return False
        state = self.dispatch.operation.progress.state
        return self.stage == 'validation' and self.dispatch.operation.terminal or self.stage == 'save' and state == 'rejected'


class CompilerProgression:
    def __init__(self, dispatcher):
        self.dispatcher, self.journal = dispatcher, dispatcher.journal
        self.store = self.journal.store

    def advance(self, principal, selection_id, *, retry_rejected=False):
        require(type(retry_rejected) is bool, 'compiler_retry_policy')
        try:
            lease = self.store.acquire(principal, selection_id, seconds=300)
        except ValueError as error:
            if str(error) != 'compiler_lease_unavailable':
                raise
            return CompilerAdvance(selection_id, 'paused', pause_reason='lease_unavailable')
        try:
            return self._advance(principal, lease, retry_rejected)
        except CompilerFenceLost:
            return CompilerAdvance(selection_id, 'paused', pause_reason='lease_lost')
        except ValueError as error:
            if str(error) != 'compiler_lease_lost':
                raise
            return CompilerAdvance(selection_id, 'paused', pause_reason='lease_lost')
        finally:
            try:
                self.store.release(principal, lease)
            except ValueError as error:
                if str(error) != 'compiler_lease_lost':
                    raise

    def _advance(self, principal, lease, retry_rejected):
        selection_id = lease.selection.effect_id
        operation = self.journal.prepare_save(principal, lease)
        stage = 'save'
        if operation.progress.state == 'saved':
            operation = self.journal.prepare_validation(principal, lease)
            stage = 'validation'
        current = self.journal.latest_round(principal, selection_id)
        # Dispatcher always reconciles original Runtime history before deciding
        # whether new-use prerequisites permit any remote effect.
        step = self.dispatcher.step(principal, lease, operation.effect.effect_id,
                                    check_id=None if current is None else current.check_id)
        blocked = CompilerAdvance(selection_id, stage, step, current, step.pause_reason)
        if step.prerequisites is None or step.prerequisites.status not in {
            'dependency_unavailable', 'eligibility_expired', 'eligibility_rejected'
        } or step.pause_reason == 'event_limit':
            return blocked
        if current is not None and current.terminal:
            rejected = any(item.progress.state == 'rejected' for item in current.operations)
            if rejected and not retry_rejected:
                return blocked
            if current.ordinal >= 16:
                return CompilerAdvance(selection_id, 'eligibility', step, current, 'round_limit')
        if current is None or current.terminal:
            ordinal = 1 if current is None else current.ordinal + 1
            current = self.journal.prepare_round(principal, lease, 'planning-check-' + str(ordinal))
        pending = current.next_operation
        require(pending is not None, 'compiler_progression_round')
        resolved = self.dispatcher.step(principal, lease, pending.effect.effect_id)
        current = self.journal.read_round(principal, selection_id, current.check_id)
        return CompilerAdvance(selection_id, 'eligibility', resolved, current, resolved.pause_reason)
