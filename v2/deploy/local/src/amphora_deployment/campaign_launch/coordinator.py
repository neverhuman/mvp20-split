"""One bounded reconciliation step; durable intent always precedes external work."""
import json
import threading

from .intent import LaunchError
from .journal import LaunchJournal
from .ports import PeerUnavailable, PreflightPort, PreflightRejected, RuntimePort, WorkersPort
from .state import utc_now


class LaunchCoordinator:
    def __init__(self, journal: LaunchJournal, preflight: PreflightPort,
                 runtime: RuntimePort, workers: WorkersPort, *, now=utc_now):
        self.journal, self.preflight = journal, preflight
        self.runtime, self.workers, self.now = runtime, workers, now
        self._lock = threading.Lock()

    def _change(self, state, transition):
        return self.journal.change(state.intent.key, state.revision, transition)

    def _move(self, state, phase, reason=None):
        return self._change(state, lambda current: current.move(phase, self.now(), reason))

    def _note(self, state, reason):
        return self._change(state, lambda current: current.note(reason, self.now()))

    def _terminal_run(self, state):
        page = self.runtime.run(state)
        plan = json.loads(state.intent.admission.canonical_bytes)['payload']['plan_sha256']
        if (page.scope != state.intent.admission.identity.scope or page.run_id != state.run_id
                or page.plan_sha256 != plan):
            raise LaunchError('launch_run_binding')
        return page.status in {'completed', 'cancelled', 'failed', 'blocked'}

    def tick(self):
        # Lifetime installation lease prevents a second coordinator process.
        # This lock also prevents overlapping background/control ticks in that owner.
        if not self._lock.acquire(blocking=False):
            return None
        try:
            state = self.journal.active()
            if state is None or state.phase == 'recovery_required':
                return state
            try:
                return self._step(state)
            except PeerUnavailable:
                return self._note(state, 'launch_peer_unavailable')
            except LaunchError as error:
                if str(error) == 'launch_revision_conflict':
                    return self.journal.get(state.intent.key)
                # Binding/validation failure latches the original identity. Never
                # call a corrupt response a rejection or silently launch afresh.
                return self._move(state, 'recovery_required', 'launch_reconciliation_required')
        finally:
            self._lock.release()

    def _step(self, state):
        if state.phase == 'preparing':
            try:
                self.preflight.check(state.intent)
            except PreflightRejected:
                return self._move(state, 'rejected', 'launch_preflight_rejected')
            return self._move(state, 'admission_unresolved')

        if state.phase == 'admission_unresolved':
            receipt = self.runtime.receipt(state.intent)
            if receipt is None:
                receipt = self.runtime.admit(state.intent)
            return self._change(state, lambda current: current.observe_admission(receipt, self.now()))

        # Missing/ambiguous run reads cannot imply completion or release capacity.
        terminal = self._terminal_run(state)
        if state.phase != 'draining' and terminal:
            return self._move(state, 'draining')

        if state.phase == 'admitted_not_engaged':
            observation = self.workers.prepare(state)
            phase = None if observation.faulted else 'engaging'
            reason = 'launch_worker_recovery_required' if observation.faulted else None
        elif state.phase == 'engaging':
            observation = self.workers.engage(state)
            phase = ('admitted_not_engaged' if observation.faulted else
                     'engaged' if observation.ready == observation.expected else None)
            reason = 'launch_worker_recovery_required' if observation.faulted else None
        elif state.phase == 'engaged':
            observation = self.workers.observe(state)
            unavailable = observation.faulted or observation.ready != observation.expected
            # Re-enter original binding reconciliation, never a new admission.
            phase = 'admitted_not_engaged' if unavailable else None
            reason = 'launch_worker_recovery_required' if unavailable else None
        elif state.phase == 'draining':
            observation = self.workers.drain(state)
            phase = 'released' if terminal and observation.quiescent else None
            reason = 'launch_worker_recovery_required' if observation.faulted else None
        else:
            raise LaunchError('launch_transition_invalid')
        return self._change(state, lambda current: current.worker_observation(
            observation, self.now(), phase=phase, reason=reason))
