"""One background coordinator owned by the existing installation supervisor."""
import threading

from ..profile import require
from .coordinator import LaunchCoordinator
from .local_readiness import LocalLaunchReadiness
from .managed_workers import ManagedLaunchWorkers
from .preflight import LaunchPreflight
from .runtime_peer import LoopbackPeer, RuntimePeer


class LaunchHost:
    def __init__(self, installation, supervisor, routes):
        self.installation, self.supervisor = installation, supervisor
        self.stop = threading.Event()
        self.thread = None
        self.failure = False
        peers = {}
        for owner in ('runtime', 'artifact', 'registry'):
            binding = supervisor.bindings[owner]
            token = binding.environment['AMPHORA_' + owner.upper() + '_OPERATOR_TOKEN']
            factory = RuntimePeer if owner == 'runtime' else LoopbackPeer
            peers[owner] = factory(routes.port(owner), token, stopped=self.stop)
        workers = ManagedLaunchWorkers(supervisor, installation.store,
            lambda supervisor, bindings: installation.catalog(supervisor, bindings, routes))
        preflight = LaunchPreflight(installation.policy, peers['runtime'], peers['artifact'], peers['registry'],
            installation.executors, LocalLaunchReadiness(installation, supervisor, self.stop))
        self.coordinator = LaunchCoordinator(installation.journal, preflight, peers['runtime'], workers)

    def start(self):
        require(self.thread is None and not self.stop.is_set(), 'launch_host_already_started')
        self.thread = threading.Thread(target=self._run, name='amphora-campaign-launch')
        self.thread.start()

    def _run(self):
        while not self.stop.is_set():
            try:
                self.coordinator.tick()
            except Exception:  # Private journal/transport details never enter control output.
                self.failure = True
                self.stop.set()
                return
            self.stop.wait(1)

    def quiesce(self):
        self.stop.set()

    def require_stopped(self):
        require(self.thread is None or not self.thread.is_alive(), 'launch_host_requires_drain')

    def close(self):
        self.quiesce()
        if self.thread is not None:
            self.thread.join(15)
        self.require_stopped()
