"""Campaign adapter over existing supervised slots; never creates a competing owner."""
from ..profile import ProfileError
from ..scientific_workers.group import ScientificGroup
from ..scientific_workers.ownership import require_configured_pending
from .intent import LaunchError
from .ports import PeerUnavailable, WorkerObservation


class ManagedLaunchWorkers:
    def __init__(self, supervisor, store, catalog_factory):
        self.supervisor, self.store, self.catalog_factory = supervisor, store, catalog_factory
        self.bound_request = None

    @staticmethod
    def _fingerprints(group):
        return {name: slot.binding.profile.fingerprint for name, slot in group.slots.items()}

    def _observation(self):
        scientific = self.supervisor.scientific.status()
        native = self.supervisor.workers.status()
        values = list(scientific.values()) + list(native.values())
        return WorkerObservation(len(values), sum(row['state'] in {'running', 'waiting', 'standby'}
            and not row['faulted'] for row in values),
            all(row['state'] == 'quiescent' and not row['faulted'] for row in values),
            any(row['faulted'] for row in values))

    def _require_bound(self, state):
        if self.bound_request != state.intent.request.sha256:
            raise LaunchError('launch_worker_binding_unavailable')
        for slot in self.supervisor.scientific.slots.values():
            slot.binding.profile.verify()

    def prepare(self, state):
        try:
            bindings = self.store.prepare(state)
            desired = {name: binding.profile.fingerprint for name, binding in bindings.items()}
            with self.supervisor.lock:
                if self.supervisor.closed:
                    raise PeerUnavailable()
                if self._fingerprints(self.supervisor.scientific) != desired:
                    self.supervisor.workers.require_quiescent()
                    # Pre-admission standby advertised real idle capacity without
                    # creating turns. Withdraw it before changing run bindings.
                    for name, row in self.supervisor.scientific.status().items():
                        if row['state'] == 'standby':
                            self.supervisor.scientific.command(name, 'quiesce')
                    self.supervisor.scientific.require_quiescent()
                    # Withdrawal runs in reporters' background threads. Poll the
                    # stopped guard; never join network work in the control lock.
                    self.supervisor.catalog.quiesce()
                    self.supervisor.catalog.require_stopped()
                    if any(slot.thread is not None and slot.thread.is_alive()
                           for slot in self.supervisor.scientific.slots.values()):
                        raise PeerUnavailable()
                    require_configured_pending(self.store.root, self.store.deployment_id,
                                               [binding.profile for binding in bindings.values()])
                    self.supervisor.scientific.detach()
                    self.supervisor.scientific = ScientificGroup(bindings)
                    self.bound_request = None
                if self.bound_request != state.intent.request.sha256:
                    require_configured_pending(self.store.root, self.store.deployment_id,
                                               [binding.profile for binding in bindings.values()])
                    self.supervisor.catalog.quiesce()
                    self.supervisor.catalog.require_stopped()
                    self.supervisor.catalog = self.catalog_factory(self.supervisor, bindings)
                    self.supervisor.scientific.adopt()
                    self.supervisor.catalog.start()
                    self.bound_request = state.intent.request.sha256
                # Recover original journals only. ScientificSlot.recover observes
                # starting/started turns; it cannot replace them with new starts.
                for group in (self.supervisor.scientific, self.supervisor.workers):
                    for name, row in group.status().items():
                        if row['faulted']:
                            try:
                                group.command(name, 'recover')
                            except ProfileError:
                                pass  # Original fault/turn remains visibly unresolved.
                return self._observation()
        except ProfileError:
            raise PeerUnavailable() from None

    def engage(self, state):
        if self.bound_request != state.intent.request.sha256:
            self.prepare(state)
        try:
            with self.supervisor.lock:
                self._require_bound(state)
                for name, row in self.supervisor.scientific.status().items():
                    if row['state'] == 'quiescent' and not row['faulted']:
                        self.supervisor.scientific_command(name, 'start')
                for name, row in self.supervisor.workers.status().items():
                    if row['state'] == 'quiescent' and not row['faulted']:
                        self.supervisor.worker_command(name, 'start')
                return self._observation()
        except ProfileError:
            raise PeerUnavailable() from None

    def observe(self, state):
        if self.bound_request != state.intent.request.sha256:
            return self.prepare(state)
        try:
            with self.supervisor.lock:
                self._require_bound(state)
                return self._observation()
        except ProfileError:
            raise LaunchError('launch_worker_binding_changed') from None

    def drain(self, state):
        # A run can finish before engagement or the controller can restart during
        # drain. Rebind/adopt its original journals before judging quiescence.
        self.prepare(state)
        with self.supervisor.lock:
            self._require_bound(state)
            self.supervisor.workers.quiesce()
            self.supervisor.scientific.quiesce()
            self.supervisor.catalog.quiesce()
            observation = self._observation()
            if observation.quiescent:
                try:
                    self.supervisor.catalog.require_stopped()
                    require_configured_pending(self.store.root, self.store.deployment_id, [])
                except ProfileError:
                    return WorkerObservation(observation.expected, 0, False)
            return observation
